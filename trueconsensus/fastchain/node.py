import os
import sys
import time
import grpc
import struct
from collections import defaultdict
from threading import Timer, Thread, Lock, Condition

from trueconsensus.dapps.bank import Bank
from trueconsensus.fastchain.ecdsa_sig import get_asymm_key
from trueconsensus.proto import request_pb2, \
    request_pb2_grpc, \
    proto_message as message

from trueconsensus.fastchain.config import config_general, \
    RL, \
    CLIENT_ADDRESS, \
    _logger

BUF_SIZE = 4096 * 8 * 8

lock = Lock()
cond = Condition(lock)


class exec_thread(Thread):
    def __init__(self, node, req):
        self.node = node
        self.req = req
        Thread.__init__(self)

    def run(self):
        self.node.execute(self.req)
        return


class req_counter:
    def __init__(self):
        self.number = 1
        self.prepared = False
        self.req = None


def serialize(req):
    size = req.ByteSize()
    b = struct.pack("!I", size)
    return b + req.SerializeToString()


def record(file, message):
    file.write(str(time.time()) + "\t" + message + "\n")


def record_pbft(node_id, file, request):
    msg = "Req Type: [%s], Seq: [%d], Received From: [%d], In View: [%d]" % (
        request.inner.type,
        request.inner.seq,
        request.inner.id,
        request.inner.view
    )
    _logger.info("Node: [%s], %s" % (node_id, msg))
    record(file, msg)


class Node(object):
    '''
    Main Node responsible for handling following PBFT phases:
    - request
    - pre-prepare
    - prepare
    - commit
    - reply
    '''

    def __init__(self, _id, view, N, block_size=10,
        committee_addresses=[], max_requests=None, max_retries=10):
        """
        @committee_addresses is a list of tuples containing the socket and ip addresses
        for all the nodes that are currently members of the committee
        """
        self.max_requests = max_requests
        self.max_retries = max_retries
        self.kill_flag = False
        # self.ecdsa_key = ecdsa_sig.get_asymm_key(0, "verify")
        self._id = _id             # id
        self.view = view         # current view number
        self.view_active = True  # If we have majority agreement on view number
        self.N = N               # total number of replicas
        self.f = int((N-1)/3)    # number of failues tolerated
        self.low_bound = 0       # lower bound for acceptable sequence numbers
        self.high_bound = 0      # upper bound for acceptable sequence numbers
        self.primary = view % N
        self.seq = 0   # next available sequence number if this node is primary
        self.last_executed = 0
        self.last_stable_checkpoint = 0
        self.checkpoint_proof = []
        self.checkpoint_interval = 100
        self.vmin = 0            # used for view changes
        self.vmax = 0
        self.waiting = {}
        self.timeout = 10*60     # time interval (seconds), before view change
        self.lock = Lock()
        # hack
        self.clientbuff = bytes()
        self.clientlock = Lock()
        self.grpc_channel_map = {}    
        self.block_size = block_size
        self.last_block_pool = []
        self.txpool = [] # actual txn pool filled from req received by the client
        self.incoming_buffer_map = defaultdict(list) # buffer for incoming requests in between phases (rounds)
        self.outgoing_buffer_map = defaultdict(list) # buffer for requests sent in between phases
        self.client_reply_pool = [] # blocks ready for transportation to the client go in this
        # message log for node communication related to the
        # PBFT protocol: [type][seq][id] -> request
        # used to prepare blocks
        self.node_message_log = {
            "PRPR": {},
            "PREP": {},
            "COMM": {},
            "INIT": {},
            "REQU": {},
            "VCHA": {},
            "NEVW": {},
            "CHKP": {},
        }
        # message log for client communication (requests)
        # [client id][timestamp] -> request
        self.client_message_log = {}
        # dictionary for prepare messages
        # (digest -> (number prepares received, 'prepared'[T/F])
        self.prep_dict = {}
        self.comm_dict = {}
        # dictionary for all requests that have prepared (seq -> request)
        self.prepared = {}
        self.active = {}      # dictionary for all currently active requests
        self.view_dict = {}   # [view num] -> [list of ids]
        # self.key_dict = {}
        self.replica_map = {}
        self.bank = Bank(id, 1000)
        self.committee_ids = committee_addresses

        self.request_types = {
            "REQU": self.process_client_request,
            "PRPR": self.process_preprepare,
            "PREP": self.process_prepare,
            "COMM": self.process_commit,
            "INIT": self.process_init,
            "VCHA": self.process_view_change,
            "NEVW": self.process_new_view,
            "CHKP": self.process_checkpoint,
        }
        # log for executed commands
        COMMIT_LOG_FILE = os.path.join(
            config_general.get("log", "root_folder"),
            "replica%s_commits.txt" % self._id
        )
        self.commitlog = open(COMMIT_LOG_FILE, 'w', 1)
        # log for debug messages
        replica_log_loc = os.path.join(
            config_general.get("log", "root_folder"),
            "replica" + str(self._id) + "_log.txt"
        )
        self.debuglog = open(replica_log_loc, 'w', 1)

    def debug_print_bank(self):
        _logger.info("Node: [%s], Wait Queue Length: [%s]" % (self._id, len(self.waiting)))
        _logger.info("Node: [%s], Last Executed: [%s]" % (self._id, self.last_executed))
        self.bank.print_balances()

    def reset_message_log(self):
        # message log for node communication related to the PBFT protocol:
        # [type][seq][id] -> request
        self.node_message_log = {
            "PRPR": {},
            "PREP": {},
            "COMM": {},
            "INIT": {},
            "REQU": {},
            "VCHA": {},
            "NEVW": {},
            "CHKP": {},
        }
        self.prep_dict = {}
        self.comm_dict = {}

    def unicast_message(self, _id, req, test_connection=False):
        retries = 0
        channel = self.replica_map[_id]
        stub = request_pb2_grpc.FastChainStub(channel)
        success = False
        while retries <= self.max_requests:
            # make the call and exit while loop, since this was just an INIT request
            try:
                if test_connection:
                    response = stub.Check(req, timeout=self.timeout)
                    # import pdb; pdb.set_trace()
                    assert response.status is 200
                    _logger.info("Node: [%s], Phase: [INIT], Msg: [Connected to Replica %d]" % (self._id, _id))
                else:
                    response = stub.Send(req)
                success = True
                break
            except Exception as E:
                _logger.error("gRPC channel for Node [%s] is not active. Retrying.. (%s)" % (_id, retries))
                _logger.error("ErrorMsg => {%s}" % E)
                retries += 1
                time.sleep(1)
        if retries > self.max_requests:
            _logger.error("Node [%s], ErrorMsg: [Max retries reached], Target Replica: [%s]" % (self._id, _id))
        if success:
            _logger.info("Node [%s], Msg: [FastChainStub.Send()], Status: [200], Target Replica: [%s]" % (self._id, _id))
            return True
        else:
            return False

    # TODO: include a failed send buffer, retry later
    def safe_send(self, node_id, req):
        self.outgoing_buffer_map[_id].append(req)

    def broadcast_to_nodes(self, req):
        counter = 0
        for i, channel in self.replica_map.items():
            if i == self._id:
                continue
            self.safe_send(i, channel, req)
            counter += 1
        msg = "broadcasted seq {} of type {} #{} times".format(str(req.inner.seq),
                                                   req.inner.type,
                                                   str(counter))
        record(self.debuglog, msg)

    def init_replica_map(self, grpc_obj):
        self.grpc_channel_map[self._id] = grpc_obj
        self.replica_map[self._id] = grpc_obj
        # TODO: 
        # make this dynamic / event responsibe upon request of addition of new node (from BFT committee)
        # Also, this should trigger check margin for valid minimum number of nodes to be present 
        # to achieve BFT fault tolerance (N-1/3)
        replica_tracker = dict.fromkeys(range(self.N), False)
        replica_tracker[self._id] = True
        for target_node in range(self.N):
            if target_node == self._id:
                continue
            remote_ip, remote_port = RL[target_node]
            channel = grpc.insecure_channel('%s:%s' % (remote_ip, remote_port))
            self.replica_map[target_node] = channel
            self.grpc_channel_map[target_node] = channel
            # instantiate buffmap[] and outbuffmap[] as we just sent out init req, 
            # which gets processed immediately. So that self.clean() doesn't act out
            # self.incoming_buffer_map[target_node].append(None)
            # self.outgoing_buffer_map[target_node].append(None)
            m = self.create_request("INIT", 0, str(self._id).encode("utf-8"), target=target_node)
            replica_tracker[target_node] = self.unicast_message(target_node, m, test_connection=True)
            # msg = "init connection to replica %d" % i
        return replica_tracker

    # type, seq, message, (optional) tag request
    def create_request(self, req_type, seq, msg, txpool=None, target=None, outer_req=None):
        key = get_asymm_key(self._id, ktype="sign")
        if not bool(key):
            _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
            return
        if req_type == "PRPR":
            m = message.add_sig(key, self._id, seq, self.view, req_type, msg, txpool=txpool)
        else:
            m = message.add_sig(key, self._id, seq, self.view, req_type, msg)
        #     import pdb; pdb.set_trace()
        # msg = bytes(msg, encoding='utf-8')
        if target:
            m.dest = target
        if outer_req:
            m.outer = outer_req.SerializeToString()
        return m

    # TODO: finish this properly
    def execute_in_order(self, req):
        waiting = True
        seq = req.inner.seq
        dig = req.inner.msg
        r = req
        client_req, t, fd = self.active[dig]
        if client_req is None:
            return
        while seq == self.last_executed + 1:
            waiting = False
            self.execute(r)
            #e = exec_thread(self, r)
            #e.start()
            self.last_executed += 1
            if seq+1 in self.waiting:
                seq += 1
                r = self.waiting[seq]
                del self.waiting[seq]

        if waiting:
            self.waiting[req.inner.seq] = r

    def try_client(self):
        ip, port = CLIENT_ADDRESS
        _logger.debug("Node: [%s], Msg: [Trying client], Target: [%s]" % \
                      (self._id, CLIENT_ADDRESS))
        while True:
            # time.sleep(5)
            self.clientlock.acquire()
            if len(self.clientbuff) > 0:
                try:
                    self.send_reply_to_client(self.clientbuff)
                    self.clientbuff = bytes()
                except Exception as E:
                    _logger.error("Node: [%s], ErrorMsg => {while trying client, encountered: %s}" % (self._id, E))
            self.clientlock.release()

    def send_reply_to_client(self, target_node):
        channel = self.grpc_channel_map[target_node]
        stub = request_pb2_grpc.Client(channel)
        response = stub.Send(n.outgoing_buffer_map[target_node], timeout=self.timeout)
        return response

    def execute(self, req):
        """
        clientbuff is used to maintain buffer for failed requests for retries
        """
        seq = req.inner.seq
        dig = req.inner.msg

        client_req, t, fd = self.active[dig]
        t.cancel()

        key = get_asymm_key(self._id, ktype="sign")
        if not bool(key):
            _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
            return
        #time.sleep(1)
        #rc = ecdsa_sig.verify(self.ecdsa_key, self.hello_sig, "Hello world!")
        #cond.acquire()
        ## Horrible hack...
        #self.last_executed = max(seq,self.last_executed)
        m = self.bank.process_request(key, self._id, seq, client_req)
        client_req.inner.msg = "TRAN00000000"
        #for i in range(1024):
        discard = self.bank.process_request(key, self._id, seq, client_req)
        #cond.release()
        #if self._id == self.primary and fd in self.grpc_channel_map:
        #if fd in self.grpc_channel_map:
        #self.safe_send(self.grpc_channel_map[fd], m)
        #self.clean(fd)
        time.sleep(0.05)
        # TODO: hack
        retry = True
        #while retry:
        self.clientlock.acquire()
        try:
            self.send_reply_to_client(self.clientbuff+serialize(m))
            self.clientbuff = bytes()
        except:
            _logger.warn("failed to send, adding to client outbuff")
            self.clientbuff += serialize(m)
            #continue
        self.clientlock.release()
        #retry = False

        record(self.debuglog, "EXECUTED " + str(seq))
        #print("adding request with sequence number " + str(req.inner.seq) + " to queue")
        if self.max_requests and seq >= self.max_requests:
            maxout_msg = "max requests reached, shutting down.."
            _logger.info(maxout_msg)
            print(maxout_msg)
            #sys.exit()
            t = Timer(5, self.suicide)
            t.start()

    def clean(self, _id):
        #print("cleaning " + str(fd))
        try:
            del self.grpc_channel_map[_id]
            # del self.incoming_buffer_map[_id]
            del self.outgoing_buffer_map[_id]
        except Exception as E:
            _logger.debug(E)

    def process_init(self, req):
        """
        adds gRPC channel instance to replica_map[req.inner.id] 
        and updates node history in log metadata
        """
        if req.inner.id < 0:
            return None
        # TODO: fix this so we can do crash recovery
        if req.inner.id not in self.replica_map:
            self.replica_map[req.inner.id] = self.grpc_channel_map[self._id]
        else:
            # TODO: verify this check 
            # (why are we wanting to update/clean only when req ID is > self ID?)
            if req.inner.id > self._id:
                self.clean(req.inner.id)
                self.replica_map[req.inner.id] = self.grpc_channel_map[self._id]
                #record_pbft(self.debuglog, req)
                self.add_node_history(req)

    def process_checkpoint(self, req, fd):
        pass

    # TODO: requests that reuse timestamps are ignored
    def in_client_history(self, req):
        if req.inner.id not in self.client_message_log:
            return False
        if req.inner.timestamp not in self.client_message_log[req.inner.id]:
            return False
        return True

    def add_client_history(self, req):
        if req.inner.id not in self.client_message_log:
            self.client_message_log[req.inner.id] = {req.inner.timestamp: req}
        else:
            self.client_message_log[req.inner.id][req.inner.timestamp] = req

    # TODO
    def handle_timeout(self, dig, view):
        self.lock.acquire()
        if self.view > view:
            return
        _logger.warn("Node: [%s], WarnMsg => {TIMEOUT TRIGGERED}" % (self._id))
        # Cancel all other timers
        client_req, t, fd = self.active[dig]
        for key, value in self.active.items():
            client_req, t, fd = value
            if key != dig:
                t.cancel()
        self.view += 1
        self.view_active = False
        self.lock.release()

        # message construction
        msg = ""
        for i in self.checkpoint_proof:
            msg += serialize(i)

        # [type][seq][id] -> req

        # for each prepared request
        for sequence, digest in self.prepared.items():
            r = self.node_message_log["PRPR"][sequence][self.primary] #old primary
            msg += serialize(r)
            counter = 0
            # for each replica until we get 2f preps
            for i in range(0, self.N):
                if counter == 2*self.f:
                    break
                try:
                    r = self.node_message_log["PREP"][sequence][i]
                    msg += serialize(r)
                    counter += 1
                except:
                    continue

        _logger.debug("Node: [%s], Msg: [Prepared Items Length - %d], MessageType: [%s], Items => {%s}" % 
            (self._id, len(msg), type(msg), self.prepared))
        # import pdb; pdb.set_trace()
        m = self.create_request("VCHA", self.last_stable_checkpoint, msg.encode("utf-8"))
        self.broadcast_to_nodes(m)
        self.process_view_change(m, 0)
        # TODO start a time for the view change operation
        # TODO set flag to stop processing requests

    def process_client_request(self, current_txn_pool):
        _logger.info("Node: [%s], Phase: [PROCESS CLIENT REQ]" % (self._id))
        # if req.inner.timestamp == 0:
        #     pass
        #     #print(req.inner.msg)
        # if req.dig in self.active:
        #     client_req, t, fd = self.active[req.dig]
        #     if client_req is None:
        #         self.active[req.dig] = (req, t, fd)
        #         if req.dig in self.comm_dict and self.comm_dict[req.dig].prepared:
        #             m = self.comm_dict[req.dig].req
        #             self.execute_in_order(m)
        #     return

        # self.lock.acquire()
        # if self.view_active:
        #     view = self.view
        # else:
        #     self.lock.release()
        #     return
        # self.add_client_history(req)
        # request_timer = Timer(self.timeout, self.handle_timeout, [req.dig, req.inner.view])
        # request_timer.daemon = True
        # request_timer.start()
        # self.active[req.dig] = (req, request_timer, fd)
        # self.lock.release()

        self.seq = self.seq+1
        m = self.create_request("PRPR", self.seq, req.dig, req, txpool=current_txn_pool)
        self.add_node_history(m)
        record_pbft(self.debuglog, m)
        self.broadcast_to_nodes(m)
        # self.block_pool.append(m)
        # if len(self.block_pool) == self.block_size:
        #     self.broadcast_to_nodes(self.block_pool)
        #     self.block_pool = []
        # TODO: if client sends to a backup, retransmit to primary
        # or not..... maybe better to save bandwidth


    def inc_prep_dict(self, digest):
        if digest in self.prep_dict:
            self.prep_dict[digest].number += 1
        else:
            self.prep_dict[digest] = req_counter()

    def inc_comm_dict(self, digest):
        if digest in self.comm_dict:
            self.comm_dict[digest].number += 1
            # self.comm_dict[digest].seq = seq
            # self.comm_dict[digest].id_list.append(id)
        else:
            self.comm_dict[digest] = req_counter()

    # return true if we are exactly at the margin to make prepared(digest) true
    # TODO: make this cleaner, 2*f isn't very convinving 
    def check_prepared_margin(self, digest, seq):
        try:
            if not self.prep_dict[digest].prepared:
                if self.prep_dict[digest].number >= 2*self.f:
                    if self.node_message_log["PRPR"][seq][self.primary].inner.msg == digest:
                        self.prep_dict[digest].prepared = True
                        return True
            return False
        except:
            return False

    # TODO: make this cleaner
    def check_committed_margin(self, digest, req):
        seq = req.inner.seq
        try:
            if not self.comm_dict[digest].prepared:
                if self.comm_dict[digest].number >= 2*self.f + 1:
                    if self.node_message_log["PRPR"][seq][self.primary].inner.msg == digest:
                        self.comm_dict[digest].prepared = True
                        self.comm_dict[digest].req = req
                        return True
            return False
        except:
            return False

    def process_preprepare(self, req, fd):
        """
        Process PrePrepare requests
        """
        _logger.info("Node: [%s], Phase: [PRE-PREPARE], Event FD: [%s]" % (self._id, fd))

        if req.inner.seq in self.node_message_log["PRPR"]:
            return None

        # the msg field for a preprepare should be the digest of the original client request
        # TODO: make it clearer that req.outer stands for the message that the replica in subject
        # is going down..
        if req.outer != b'': # req.outer should be same format as req.inner (bytes)
            try:
                # import pdb; pdb.set_trace()
                client_req = request_pb2.Request()
                # client_req.ParseFromString(req.outer)
                client_req.ParseFromString(req)
                record_pbft(self.debuglog, client_req)
                client_key = get_asymm_key(client_req.inner.id, ktype="sign")
                if not bool(client_key):
                    _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                    return
                client_req = message.check(client_key, client_req)
                if client_req == None or req.inner.msg != client_req.dig:
                    _logger.warn("FAILED PRPR OUTER SIGCHECK")
                    return
            except:
                _logger.error("ERROR IN PRPR OUTER PROTOBUFF")
                raise
                # return
            # TODO: remove replica from replica map as it has by this time probably gone down or is corrupt.
        else:
            client_req = None
        if req.inner.msg not in self.active:
            # self.active[req.inner.msg] = (client_req, Timer(self.timeout, self.handle_timeout), fd)
            request_timer = Timer(self.timeout, self.handle_timeout, [req.inner.msg, req.inner.view])
            request_timer.daemon = True
            request_timer.start()
            self.active[req.inner.msg] = (client_req, request_timer, fd)

        self.add_node_history(req)
        m = self.create_request("PREP", req.inner.seq, req.inner.msg)
        self.add_node_history(m)
        record_pbft(self.debuglog, m)
        self.inc_prep_dict(req.inner.msg)
        self.broadcast_to_nodes(m)

        if self.check_prepared_margin(req.inner.msg, req.inner.seq):
            record(self.debuglog, "PREPARED sequence number " + str(req.inner.seq))
            m = self.create_request("COMM", req.inner.seq, req.inner.msg)
            self.broadcast_to_nodes(m)
            self.add_node_history(m)
            self.inc_comm_dict(m.inner.msg)
            record_pbft(self.debuglog, m)
            self.prepared[req.inner.seq] = req.inner.msg
            if self.check_committed_margin(m.inner.msg, m):
                record(self.debuglog, "COMMITTED sequence number " + str(m.inner.seq))
                record_pbft(self.commitlog, m)
                self.execute_in_order(m)

    def process_prepare(self, req, fd):
        """
        Process Prepare requests
        """
        _logger.info("Node: [%s], Phase: [PREPARE], Event FD: [%s]" % (self._id, fd))
        self.add_node_history(req)
        self.inc_prep_dict(req.inner.msg)
        # import pdb; pdb.set_trace()
        # TODO: this turns out to be false always
        if self.check_prepared_margin(req.inner.msg, req.inner.seq):
            record(self.debuglog, "PREPARED sequence number " + str(req.inner.seq))
            m = self.create_request("COMM", req.inner.seq, req.inner.msg)
            self.broadcast_to_nodes(m)
            self.add_node_history(m)
            self.inc_comm_dict(m.inner.msg)
            record_pbft(self.debuglog, m)
            self.prepared[req.inner.seq] = req.inner.msg
            if self.check_committed_margin(m.inner.msg, m):
                record(self.debuglog, "COMMITTED sequence number " + str(m.inner.seq))
                record_pbft(self.commitlog, m)
                self.execute_in_order(m)

    def process_commit(self, req, fd):
        """
        Process Commit requests in New view
        """
        _logger.info("Node: [%s], Phase: [COMMIT], Event DF: [%s]" % (self._id, fd))

        self.add_node_history(req)
        self.inc_comm_dict(req.inner.msg)
        if self.check_committed_margin(req.inner.msg, req):
            record(self.debuglog, "COMMITTED sequence number " + str(req.inner.seq))
            record_pbft(self.commitlog, req)
            self.execute_in_order(req)


    def vprocess_checkpoints(self, vcheck_list, last_checkpoint):
        """
        Process Checkpoints requests in New view
        """
        #rc = vprocess_checkpoints(vcheck_list, r.inner.seq)
        if last_checkpoint == 0:
            return True
        if len(vcheck_list) <= 2*self.f:
            return False
        dig = vcheck_list[0].inner.msg
        for c in vcheck_list:
            if c.inner.seq != last_checkpoint or c.inner.msg != dig:
                return False
        return True


    #vprocess_prepare(vprep_dict, vpre_dict, r.inner.seq)
    def vprocess_prepare(self, vprep_dict, vpre_dict, last_checkpoint):
        """
        Process Prepare requests in New view
        """
        max = 0
        #[seq][id] -> req
        counter = {}
        for k1,v1 in vprep_dict.items():
            if (not k1 in vpre_dict):
                return False,0
            dig = vpre_dict[k1].inner.msg
            key = get_asymm_key(vpre_dict[k1].inner.id, ktype="sign")
            if not bool(key):
                _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                return
            r = message.check(key, vpre_dict[k1])
            if r == None:
                return False,0

            for k2,v2 in v1.items():
                # check sigs
                key = get_asymm_key(v2.inner.id, ktype="sign")
                if not bool(key):
                    _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                    return
                r = message.check(key,v2)
                if r == None:
                    return False,0
                #prepares need to be for the same digest
                if r.inner.msg != dig:
                    return False
                if (vpre_dict[k1].inner.id == r.inner.id):
                    return False,0
                if r.inner.seq < last_checkpoint:
                    return False,0
                if r.inner.seq > max:
                    max = r.inner.seq

                if r.inner.seq not in counter:
                    counter[r.inner.seq] = 1
                else:
                    counter[r.inner.seq] += 1

        for k in counter:
            if counter[k] < 2*self.f:
                return False,0
            self.add_node_history(vpre_dict[k])
        return True,max

    def in_view_dict(self,req):
        if req.inner.view not in self.view_dict:
            return False
        for m in self.view_dict[req.inner.view][0]:
            if m.inner.id == req.inner.id:
                return True
        return False

    #m = self.create_request("VCHA", self.last_stable_checkpoint, msg)
    def process_view_change(self, req, fd):
        _logger.warn("Node: [%s], Phase: [PROCESS VIEW CHANGE], Event FD: [%s], RequestInnerID: [%s]" % (self._id, fd, req.inner.id))
        _logger.warn("Node: [%s], RequestInnerView: [%s]" % (self._id, req.inner.view))
        self.add_node_history(req)
        new_v = req.inner.view
        if self._id != req.inner.view or new_v < self.view:
            return


        # (NEVW, v+1, V, O) where V is set of valid VCHA, O is set of PRPR
        #TODO (NO PIGGYBACK)
        # determine the latest stable checkpoint
        checkpoint = 0
        # [seq][id] -> req
        # for each view change message
        #for r in self.view_dict[new_v]:
        vcheck_list = []
        vpre_dict = {}
        vprep_dict = {}
        m = req.inner.msg
        # for each chkp, prpr, prep message it contains
        while len(m) > 0:
            b = m[:4]
            size = struct.unpack("!I", b)[0]
            try:
            #if True:
                r2 = request_pb2.Request()
                r2.ParseFromString(m[4:size+4])
                record_pbft(self.debuglog, r2)
                key = get_asymm_key(r2.inner.id, ktype="sign")
                if not bool(key):
                    _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                    return
                r2 = message.check(key, r2)
                if r2 is None:
                    print("FAILED SIG CHECK IN VIEW CHANGE")
                    return
            except Exception as E:
            #else:
                r2 = None
                print("FAILED PROTOBUF EXTRACT IN VIEW CHANGE: %s" % E)
                raise
                return

            if r2.inner.type == "CHKP":
                vcheck_list.append(r2)
            if r2.inner.type == "PREP":
                if r2.inner.seq not in vprep_dict:
                    vprep_dict[r2.inner.seq] = {r2.inner.id: r2}
                else:
                    vprep_dict[r2.inner.seq][r2.inner.id] = r2
            if r2.inner.type == "PRPR":
                vpre_dict[r2.inner.seq] = r2
            m = m[size+4:]

        rc1 = self.vprocess_checkpoints(vcheck_list, req.inner.seq)
        rc2,max = self.vprocess_prepare(vprep_dict, vpre_dict, req.inner.seq)
        # on success add to list
        # on error do nothing and return
        # request list, min, max
        if rc1 and rc2:
            if new_v not in self.view_dict:
                self.view_dict[new_v] = ([req],0,0)
            else:
                if not self.in_view_dict(req):
                    self.view_dict[new_v][0].append(req)

        # set min and max
        if self.view_dict[new_v][1] < req.inner.seq:
            #self.view_dict[new_v][1] = req.inner.seq
            temp = self.view_dict[new_v]
            self.view_dict[new_v] = (temp[0], req.inner.seq, temp[2])
        if self.view_dict[new_v][2] < max:
            #self.view_dict[new_v][2] = max
            temp = self.view_dict[new_v]
            self.view_dict[new_v] = (temp[0], temp[1], max)
        # proccess and send the new view request
        if ((not self.view_active) or new_v > self.view) and len(self.view_dict[new_v][0]) > 2*self.f:
            msg = ""
            for i in self.view_dict[new_v][0]:
                msg += serialize(i)
            for i in range(self.view_dict[new_v][1], self.view_dict[new_v][2]):
                if i == 0:
                    continue
                r = self.node_message_log["PRPR"][i][self.primary]
                temp = self.create_request("PRPR", i, r.inner.msg)
                msg += serialize(temp)
            out = self.create_request("NEVW", 0, msg)
            self.view_active = True
            self.primary = self.view % self.N
            self.active = {}
            self.reset_message_log()
            #TODO: MOve this check to execute
            self.client_message_log = {}
            self.prepared = {}
            self.seq = self.view_dict[new_v][2]
            self.broadcast_to_nodes(out)
            print("Entering New view", self.view)

    def nvprocess_prpr(self, prpr_list):
        """
        Process PrePrepare requests in New view
        """
        for r in prpr_list:
            key = get_asymm_key(r.inner.id, ktype="sign")
            if not bool(key):
                _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                return
            m = message.check(key, r)
            if m == None:
                return False
            out = self.create_request("PREP", r.inner.seq, r.inner.msg)
            self.broadcast_to_nodes(out)
            #TODO: add view to node_message_log, don't broadcast here
            #if self._id in self.node_message_log["COMM"][r.inner.seq]:
            #    out = self.create_request("COMM", r.inner.seq, r.inner.msg)
            #    self.broadcast_to_nodes(out)
        return True

    #TODO: check each message for correctness?  Shouldn't be necessary...
    def nvprocess_view(self, vchange_list):
        for r in vchange_list:
            key = get_asymm_key(r.inner.id, ktype="sign")
            if not bool(key):
                _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                return
            m = message.check(key, r)
            if m == None:
                return False
        return True

    def process_new_view(self, req, fd):
        _logger.info("Node: [%s], Phase: [PROCESS NEW VIEW], Event FD: [%s], RequestInnerID: [%s]" % (self._id, fd, req.inner.id))
        # parse requests by type
        m = req.inner.msg
        vchange_list = []
        prpr_list = []
        # counter = 0
        while len(m) > 0:
            # counter += 1
            # _logger.info("Node: [%s], Phase: [PROCESS NEW VIEW], Event FD: [%s], RequestInnerID: [%s]" % (self._id, fd, req.inner.id))
            # _logger.info("COUNTER [%s]" % counter)
            b = m[:4]
            size = struct.unpack("!I",b)[0]
            try:
                r2 = request_pb2.Request()
                r2.ParseFromString(m[4:size+4])
                record_pbft(self.debuglog, r2)
                key = get_asymm_key(r2.inner.id, ktype="sign")
                if not bool(key):
                    _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                    return
                r2 = message.check(key, r2)
                if r2 == None:
                    _logger.warn("FAILED SIG CHECK IN NEW VIEW")
                    return
            except:
                r2 = None
                _logger.warn("FAILED PROTOBUF EXTRACT IN NEW VIEW")
                return

            if r2.inner.type == "VCHA":
                vchange_list.append(r2)
            if r2.inner.type == "PRPR":
                prpr_list.append(r2)
            m = m[size+4:]

        if not self.nvprocess_view(vchange_list):
            _logger.warn("FAILED VCHANGE VALIDATION IN NEW VIEW")
            return

        if req.inner.view >= self.view:
            self.view = req.inner.view
            self.view_active = True
            self.primary = self.view % self.N
            self.active = {}
            self.reset_message_log()
            #TODO: Move this check to execute
            self.client_message_log = {}
            self.prepared = {}
            rc2 = self.nvprocess_prpr(prpr_list)
            _logger.info("Node: [%s], Msg: [New View Accepted], View: [%s]" % (self._id, self.view))

        return

    # [type][seq][id] -> request
    def add_node_history(self, req):
        """
        Used to add consistency for buffer of requests
        """
        # if TYPE (INIT, PRPR, ..) not in node_message_log
        if req.inner.type not in self.node_message_log:
            self.node_message_log[req.inner.type] = {req.inner.seq : {req.inner.id : req}}
        else:
            # if TYPE is present, but not SEQUENCE
            if req.inner.seq not in self.node_message_log[req.inner.type]:
                self.node_message_log[req.inner.type][req.inner.seq] = {req.inner.id : req}
            else:
                # IF TYPE & SEQUENCE present, but not req.inner.id 
                self.node_message_log[req.inner.type][req.inner.seq][req.inner.id] = req

    def in_node_history(self, req):
        if req.inner.type not in self.node_message_log:
            return False
        if req.inner.seq not in self.node_message_log[req.inner.type]:
            return False
        if req.inner.id in self.node_message_log[req.inner.type][req.inner.seq]:
            return True

    def parse_request(self, req):
        # attempt to reconstruct the request object
        # close connection and return on failure
        try:
            # req = request_pb2.Request()
            # req.ParseFromString(request_bytes)
            # _logger.debug(req)
            _logger.info("Node: [%s], Phase: [PARSE REQUEST], RequestInnerID: [%s]" % (self._id, req.inner.id))
            # import pdb; pdb.set_trace()
            record_pbft(self._id, self.debuglog, req)
            key = get_asymm_key(req.inner.id, ktype="sign")
            # if not isinstance(key, ecdsa.SigningKey):
            if not bool(key):
                _logger.error("Node: [%s], ErrorMsg => {get_asymm_key(): -> returned empty key}" % (self._id))
                return
            req = message.check(key, req)
            if req is None:
                _logger.error("Node: [%s], ErrorMsg => {Failed message sig check. 'req' is empty..}" % (self._id))
                return
        except Exception as E:
            req = None
            _logger.error("Node: [%s], ErrorMsg => {ERROR IN PROTOBUF TYPES: %s}" % (self._id, E))
            # raise  # for debug
            # self.clean()
            return
        # print(req.inner.type, len(request_bytes))
        # TODO: Check for view number and view change, h/H
        if req.inner.view != self.view or not self.view_active:
            if req.inner.type != "VCHA" and req.inner.type != "NEVW" and \
                    req.inner.type != "CHKP" and req.inner.type != "REQU":
                debug_msg = "TYPE: %s - ID %s - SEQ %s - VIEW - %s" % (
                    req.inner.type,
                    req.inner.id,
                    req.inner.seq,
                    req.inner.view
                )
                _logger.warn("Bad view number - %s" % debug_msg)
                # TODO: trigger view change
                return
        if self.in_node_history(req):
            _logger.warn("Node: [%s], Msg: [Duplicate node message], Duplicate: [%s]" % 
                (self._id, req.inner.id))
        if req.inner.type in self.request_types and not self.in_client_history(req):
            # call to actual success
            self.request_types[req.inner.type](req)
        else:
            self.clean(req.inner.id)
            _logger.warn("BAD MESSAGE TYPE - %s - %s" % (
                req.inner.type,
                req.inner.id))
