import os
import sys
import time
import errno
import socks
import struct
import socket
import select
import signal
import logging
import traceback
import threading
from Crypto.Hash import SHA256
from threading import Timer, Thread, Lock, Condition

import sig
import bank
import ecdsa_sig
import request_pb2
import proto_message as message
from config import config_general, \
    RL, \
    client_address

BUF_SIZE = 4096 * 8 * 8
recv_mask = select.EPOLLIN | select.EPOLLPRI | select.EPOLLRDNORM
send_mask = select.EPOLLOUT | select.EPOLLWRNORM

lock = Lock()
cond = Condition(lock)


class exec_thread(Thread):
    def __init__(self, node, req):
        self.node = node
        self.req = req
        Thread.__init__(self)

    def run(self):
        self.node.execute(self.req)
        # print(self.req.inner.seq)
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


def record_pbft(file, request):
    msg = request.inner.type + " " + str(request.inner.seq) + " received from " + str(request.inner.id) + " in view " + str(request.inner.view)
    record(file, msg)


class node:
    def debug_print_bank(self, signum, flag):
        print(len(self.waiting))
        print("last executed: ", self.last_executed)
        self.bank.print_balances()
        # m = self.create_request("REQU", 0, "replica " + str(self.id) + " going down", 0)
        # self.broadcast_to_nodes(m)
        # for i,s in self.replica_map.iteritems():
        #    try:
        #        s.send(serialize(m))
        #        print("sent to ", i)
        #        print("-------------")
        #    except:
        #        print("could not send to ", i)
        #        #print(traceback.format_exc())
        #        print("-------------")
        sys.exit()

    def __init__(self, id, view, N, max_requests=None):
        self.max_requests = max_requests
        self.kill_flag = False
        # self.ecdsa_key = ecdsa_sig.get_asymm_key(0, "verify")
        # f = open("hello_0.dat", 'r')
        # self.hello_sig = f.read()
        # f.close()
        self.connections = 0
        # signal.signal(signal.SIGINT, self.debug_print_bank)
        self.id = id             # id
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
        self.clientbuff = ""
        self.clientlock = Lock()

        self.fdmap = {}    # file descriptor to socket mapping
        self.buffmap = {}  # file descriptor to incomming (recv) buffer mapping
        self.outbuffmap = {}
        self.p = select.epoll()                 # epoll object
        # message log for node communication related to the
        # PBFT protocol: [type][seq][id] -> request
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
        self.key_dict = {}
        self.replica_map = {}
        self.bank = bank.bank(id, 1000)

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
        COMMIT_LOG_FILE = os.path.join(config_general.get("log", "root_folder"),
                                       "replica%s_commits.txt" % self.id)
        self.commitlog = open(COMMIT_LOG_FILE, 'wb', 1)
        # log for debug messages
        self.debuglog = open("replica" + str(self.id) + "_log.txt", 'wb', 1)

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
    # TODO: include a failed send buffer per socket, retry later
    def safe_send(self, s, req):
        try:
            self.outbuffmap[s.fileno()] += serialize(req)
            self.p.modify(s.fileno(), send_mask)
        except socket.error as serr:
            print(serr)
            return
        #try:
        #    s.send(serialize(req))
        #except socket.error, serr:
        #    print(serr)
        #    #raise
        #    if serr.errno == errno.ECONNRESET or errno.EPIPE or errno.ENOTCONN:
        #        return

    def broadcast_to_nodes(self, req):
        counter = 0
        for i, sock in self.replica_map.iteritems():
            if i == self.id:
                continue
        self.safe_send(sock, req)
        counter += 1
        msg = "broadcasting {} {} {} times".format(str(req.inner.seq),
                                                   req.inner.type,
                                                   str(counter))
        record(self.debuglog, msg)


    def init_replica_map(self):
        host = socket.gethostname()
        # import pdb; pdb.set_trace()
        ip, port = RL[self.id-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))  # on EC2 we cannot directly bind on public addr
        s.listen(50)
        s.setblocking(0)
        print("Server " + str(self.id) + " listening on port " + str(port))
        print("IP: " + ip)

        self.fdmap[s.fileno()] = s
        self.p.register(s, recv_mask)
        self.replica_map[self.id] = s
        #self.replica_map = {}
        #for i in range(self.id+1, self.N)[::-1]:
        for i in range(0, self.N):
            if i == self.id:
                continue
            # r = socket.socket()
            remote_ip, remote_port = RL[i]
            print("trying to connect", RL)
            retry = True
            count = 0
            while retry:  # re-trying will not cause a deadlock.
                count += 1
                try:
                    r = socks.socksocket()
                    # import pdb; pdb.set_trace()
                    # r.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", config.TOR_SOCKSPORT[self.id], True)
                    # r.setblocking(0)
                    r.connect((remote_ip, remote_port))
                except Exception as e:
                    time.sleep(0.5)
                    r.close()
                    print("trying to connect to %s : %d, caused by %s" % (remote_ip, remote_port, str(e)))
                    #if count == 10000:
                     #   raise
                    continue
                retry = False
           #r.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            self.replica_map[i] = r
            self.fdmap[r.fileno()] = r
            self.buffmap[r.fileno()] = ""
            self.outbuffmap[r.fileno()] = ""
            self.p.register(r, recv_mask)
            #m = message.add_sig(K, "INIT " + str(ID), ID)
            #m = add_sig(0,"INIT",str(ID))
            #r.send(m.SerializeToString())
            m = self.create_request("INIT", 0, str(self.id))
            self.safe_send(r, m)
            print("init connection to replica " + str(i) + " on fd " + str(r.fileno()))

    # def init_keys(self, number):
    #     for i in range(number):
    #         key = sig.get_signing_key(i)
    #         self.key_dict[i] = key

    # type, seq, message, (optional) tag request
    def create_request(self, req_type, seq, msg, outer_req=None):
        key = self.key_dict[self.id]
        m = message.add_sig(key, self.id, seq, self.view, req_type, msg)
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

    def suicide(self):
        #time.sleep(5)
        #self.kill_flag = True
        os.kill(os.getpid(), signal.SIGINT)

    def try_client(self):
        ip, port = client_address
        while True:
            time.sleep(5);
            self.clientlock.acquire()
            if len(self.clientbuff) > 0:
                try:
                    print("trying client again...", ip, port)
                    client_sock.connect((ip, port))
                    client_sock.send(self.clientbuff)
                    client_sock.close()
                    self.clientbuff = ""
                except:
                    pass
            self.clientlock.release()


    def execute(self, req):
        seq = req.inner.seq
        dig = req.inner.msg

        client_req,t,fd = self.active[dig]
        t.cancel()

        key = self.key_dict[self.id]
        #time.sleep(1)
        #rc = ecdsa_sig.verify(self.ecdsa_key, self.hello_sig, "Hello world!")
        #cond.acquire()
        ## Horrible hack...
        #self.last_executed = max(seq,self.last_executed)
        m = self.bank.process_request(key, self.id, seq, client_req)
        client_req.inner.msg = "TRAN00000000"
        #for i in range(1024):
        discard = self.bank.process_request(key, self.id, seq, client_req)
        #cond.release()
        #if self.id == self.primary and fd in self.fdmap:
        #if fd in self.fdmap:
        #self.safe_send(self.fdmap[fd], m)
        #self.clean(fd)
        time.sleep(0.05)
        if self.max_requests and seq > self.max_requests:
            return
        client_sock = socks.socksocket() # socket.socket()
        # import pdb; pdb.set_trace()
        client_sock.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", config.TOR_SOCKSPORT[self.id], True)
        ip, port = client_address
        #TODO: hack
        retry = True
        #while retry:
        self.clientlock.acquire()
        try:
            client_sock.connect((ip, port))
            client_sock.send(self.clientbuff+serialize(m))
            client_sock.close()
            self.clientbuff = ""
        except:
            print("failed to send, adding to client outbuff")
            self.clientbuff += serialize(m)
            #continue
        self.clientlock.release()
        #retry = False

        record(self.debuglog, "EXECUTED " + str(seq))
        #print("adding request with sequence number " + str(req.inner.seq) + " to queue")
        if self.max_requests and seq >= self.max_requests:
            print("max requests reached, shutting down..")
            #sys.exit()
            t = Timer(5, self.suicide)
            t.start()

    def clean(self, fd):
        #print("cleaning " + str(fd))
        self.p.unregister(fd)
        self.fdmap[fd].close()
        del self.fdmap[fd]
        del self.buffmap[fd]
        del self.outbuffmap[fd]
        self.connections -= 1
        #print(self.connections)

    def process_init(self, req, fd):
        if req.inner.id < 0:
            return None
        #TODO: fix this so we can do crash recovery
        if not req.inner.id in self.replica_map:
            self.replica_map[req.inner.id] = self.fdmap[fd]
        else:
            if req.inner.id > self.id:
                self.clean(self.replica_map[req.inner.id].fileno())
                self.replica_map[req.inner.id] = self.fdmap[fd]
                #record_pbft(self.debuglog, req)
                self.add_node_history(req)
                print("init connection with replica " + str(req.inner.id) + " on fd " + str(fd))

    def process_checkpoint(self, req, fd):
        pass

    # TODO: requests that reuse timestamps are ignored
    def in_client_history(self, req):
        if not req.inner.id in self.client_message_log:
            return False
        if not req.inner.timestamp in self.client_message_log[req.inner.id]:
            return False
        return True

    def add_client_history(self, req):
        if not req.inner.id in self.client_message_log:
            self.client_message_log[req.inner.id] = {req.inner.timestamp : req}
        else:
            self.client_message_log[req.inner.id][req.inner.timestamp] = req

    #TODO
    def handle_timeout(self, dig, view):
        self.lock.acquire()
        if self.view > view:
            return
        print("TIMEOUT TRIGGERED")
        # Cancel all other timers
        client_req,t,fd = self.active[dig]
        for key, value in self.active.iteritems():
            client_req,t,fd = value
            if key != dig:
                t.cancel()
        self.view += 1
        self.view_active = False
        self.lock.release()

        # message construction
        msg = ""
        for i in self.checkpoint_proof:
            msg += serialize(i)

        #[type][seq][id] -> req

        # for each prepared request
        for sequence, digest in self.prepared.iteritems():
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

        print("DEBUG: " + str(len(msg)))
        m = self.create_request("VCHA", self.last_stable_checkpoint, msg)
        self.broadcast_to_nodes(m)
        self.process_view_change(m, 0)
        #TODO start a time for the view change operation
        #TODO set flag to stop processing requests

    def process_client_request(self, req, fd):
        #print("PROCESSING CLIENT REQUEST")
        if req.inner.timestamp == 0:
            pass
            #print(req.inner.msg)
        if req.dig in self.active:
            client_req, t, fd = self.active[req.dig]
            if client_req is None:
                self.active[req.dig] = (req, t, fd)
                if req.dig in self.comm_dict and self.comm_dict[req.dig].prepared:
                    m = self.comm_dict[req.dig].req
                    self.execute_in_order(m)
            return

        self.lock.acquire()
        if self.view_active:
            view = self.view
        else:
            self.lock.release()
            return
        self.add_client_history(req)
        request_timer = Timer(self.timeout, self.handle_timeout, [req.dig, req.inner.view])
        request_timer.daemon = True
        request_timer.start()
        self.active[req.dig] = (req, request_timer, fd)
        self.lock.release()

        if self.primary == self.id:
            self.seq = self.seq+1
            #m = self.create_request("PRPR", self.seq, req.dig, req)
            m = self.create_request("PRPR", self.seq, req.dig)
            self.add_node_history(m)
            record_pbft(self.debuglog, m)
            self.broadcast_to_nodes(m)
        #TODO: if client sends to a backup, retransmit to primary
        # or not..... maybe better to save bandwidth


    def inc_prep_dict(self, digest):
        if digest in self.prep_dict:
            self.prep_dict[digest].number += 1
        else:
            self.prep_dict[digest] = req_counter()

    def inc_comm_dict(self, digest):
        if digest in self.comm_dict:
            self.comm_dict[digest].number += 1
            #self.comm_dict[digest].seq = seq
            #self.comm_dict[digest].id_list.append(id)
        else:
            self.comm_dict[digest] = req_counter()

    # return true if we are exactly at the margin to make prepared(digest) true
    # TODO: make this cleaner
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
        if req.inner.seq in self.node_message_log["PRPR"]:
            return None

        # the msg field for a preprepare should be the digest of the original client request
        if req.outer != "":
            try:
                client_req = request_pb2.Request()
                client_req.ParseFromString(req.outer)
                record_pbft(self.debuglog, client_req)
                client_key = self.key_dict[client_req.inner.id]
                client_req = message.check(client_key, client_req)
                if client_req == None or req.inner.msg != client_req.dig:
                    print("FAILED PRPR OUTER SIGCHECK")
                    return
            except:
                print("ERROR IN PRPR OUTER PROTOBUFF")
                raise
        else:
            client_req = None
        if not req.inner.msg in self.active:
            #self.active[req.inner.msg] = (client_req, Timer(self.timeout, self.handle_timeout), fd)
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
        self.add_node_history(req)
        self.inc_prep_dict(req.inner.msg)
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
        self.add_node_history(req)
        self.inc_comm_dict(req.inner.msg)
        if self.check_committed_margin(req.inner.msg, req):
            record(self.debuglog, "COMMITTED sequence number " + str(req.inner.seq))
            record_pbft(self.commitlog, req)
            self.execute_in_order(req)


    #rc = vprocess_checkpoints(vcheck_list, r.inner.seq)
    def vprocess_checkpoints(self, vcheck_list, last_checkpoint):
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
        max = 0
        #[seq][id] -> req
        counter = {}
        for k1,v1 in vprep_dict.iteritems():
            if (not k1 in vpre_dict):
                return False,0
            dig = vpre_dict[k1].inner.msg
            key = self.key_dict[vpre_dict[k1].inner.id]
            r = message.check(key, vpre_dict[k1])
            if r == None:
                return False,0

            for k2,v2 in v1.iteritems():
                # check sigs
                key = self.key_dict[v2.inner.id]
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
        if not req.inner.view in self.view_dict:
            return False
        for m in self.view_dict[req.inner.view][0]:
            if m.inner.id == req.inner.id:
                return True
        return False

    #m = self.create_request("VCHA", self.last_stable_checkpoint, msg)
    def process_view_change(self, req, fd):
        print("Received a view change req from " + str(req.inner.id))
        print(req.inner.view)
        self.add_node_history(req)
        new_v = req.inner.view
        if self.id != req.inner.view or new_v < self.view:
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
            size = struct.unpack("!I",b)[0]
            try:
            #if True:
                r2 = request_pb2.Request()
                r2.ParseFromString(m[4:size+4])
                record_pbft(self.debuglog, r2)
                key = self.key_dict[r2.inner.id]
                r2 = message.check(key,r2)
                if r2 == None:
                    print("FAILED SIG CHECK IN VIEW CHANGE")
                    return
            except:
            #else:
                r2 = None
                print("FAILED PROTOBUF EXTRACT IN VIEW CHANGE")
                raise
                return

            if r2.inner.type == "CHKP":
                vcheck_list.append(r2)
            if r2.inner.type == "PREP":
                if not r2.inner.seq in vprep_dict:
                    vprep_dict[r2.inner.seq] = {r2.inner.id : r2}
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
        for r in prpr_list:
            key = self.key_dict[r.inner.id]
            m = message.check(key, r)
            if m == None:
                return False
            out = self.create_request("PREP", r.inner.seq, r.inner.msg)
            self.broadcast_to_nodes(out)
            #TODO: add view to node_message_log, don't broadcast here
            #if self.id in self.node_message_log["COMM"][r.inner.seq]:
            #    out = self.create_request("COMM", r.inner.seq, r.inner.msg)
            #    self.broadcast_to_nodes(out)
        return True

    #TODO: check each message for correctness?  Shouldn't be necessary...
    def nvprocess_view(self, vchange_list):
        for r in vchange_list:
            key = self.key_dict[r.inner.id]
            m = message.check(key, r)
            if m == None:
                return False
        return True

    def process_new_view(self, req, fd):
        print("Received a new_view from " + str(req.inner.id))
        # parse requests by type
        m = req.inner.msg
        vchange_list = []
        prpr_list = []
        counter = 0
        while len(m) > 0:
            counter += 1
            print("COUNTER", counter)
            b = m[:4]
            size = struct.unpack("!I",b)[0]
            try:
                r2 = request_pb2.Request()
                r2.ParseFromString(m[4:size+4])
                record_pbft(self.debuglog, r2)
                key = self.key_dict[r2.inner.id]
                r2 = message.check(key,r2)
                if r2 == None:
                    print("FAILED SIG CHECK IN NEW VIEW")
                    return
            except:
                r2 = None
                print("FAILED PROTOBUF EXTRACT IN NEW VIEW")
                return

            if r2.inner.type == "VCHA":
                vchange_list.append(r2)
            if r2.inner.type == "PRPR":
                prpr_list.append(r2)
            m = m[size+4:]

        if not self.nvprocess_view(vchange_list):
            print("FAILED VCHANGE VALIDATION IN NEW VIEW")
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
            print("New view ", self.view, "accepted")
        return


    # [type][seq][id] -> request
    def add_node_history(self, req):
        if not req.inner.type in self.node_message_log:
            self.node_message_log[req.inner.type] = {req.inner.seq : {req.inner.id : req}}
        else:
            if not req.inner.seq in self.node_message_log[req.inner.type]:
                self.node_message_log[req.inner.type][req.inner.seq] = {req.inner.id : req}
            else:
                self.node_message_log[req.inner.type][req.inner.seq][req.inner.id] = req

    def in_node_history(self, req):
        if not req.inner.type in self.node_message_log:
            return False
        if not req.inner.seq in self.node_message_log[req.inner.type]:
            return False
        if req.inner.id in self.node_message_log[req.inner.type][req.inner.seq]:
            return True

    def parse_request(self, request_bytes, fd):
        # attempt to reconstruct the request object
        # close connection and return on failure
        try:
            req = request_pb2.Request()
            req.ParseFromString(request_bytes)
            record_pbft(self.debuglog, req)
            key = self.key_dict[req.inner.id]
            req = message.check(key,req)
            if req == None:
                print("FAILED SIG CHECK SOMEWHERE")
                return
        except:
            req = None
            print("ERROR IN PROTOBUF TYPES")
            raise  # for debug
            self.clean(fd)
            return
        #print(req.inner.type, len(request_bytes))
        # TODO: Check for view number and view change, h/H
        if req.inner.view != self.view or not self.view_active:
            if req.inner.type != "VCHA" and req.inner.type != "NEVW" and req.inner.type != "CHKP" and req.inner.type != "REQU":
                print("Bad view number", "TYPE:",req.inner.type,"ID", req.inner.id,"SEQ",req.inner.seq, "VIEW", req.inner.view)
                return
        if self.in_node_history(req):
            #print("Duplicate node message")
            #return
            pass
        if req.inner.type in self.request_types and not self.in_client_history(req):
            self.request_types[req.inner.type](req, fd)
        else:
            self.clean(fd)
            print("BAD MESSAGE TYPE ..." + req.inner.type + "..." + str(req.inner.id))


    def server_loop(self):
        counter = 0
        #host = socket.gethostname()
        #ip,port = RL[self.id]
        #s = socket.socket()
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #s.bind(('0.0.0.0', port))  # on EC2 we cannot directly bind on public addr
        #s.listen(50)
        #s.setblocking(0)
        #print("Server " + str(self.id) + " listening on port " + str(port))
        #print("IP: " + ip)

        #self.fdmap[s.fileno] = s
        #self.p.register(s, recv_mask)
        s = self.replica_map[self.id]
        t = Timer(5, self.try_client)
        t.start()
        while True:
            #print(counter)
            events = self.p.poll()
            #print("--------")
            #cstart = time.time()
            for fd, event in events:
                counter += 1
                # need the flag for "Service temporarilly unavailable" exception
                data = None
                recv_flag = False
                if fd is s.fileno():
                    c,addr = s.accept()
                    #logging.debug("Got connection from "+ str(addr))
                    #print("Got connection from " + str(addr))
                    c.setblocking(0)
                    #c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
                    self.p.register(c, recv_mask)
                    self.fdmap[c.fileno()] = c
                    self.buffmap[c.fileno()] = ""
                    self.outbuffmap[c.fileno()] = ""
                    self.connections += 1
                else:
                    # if we have a write event
                    if event & send_mask != 0:
                        if len(self.outbuffmap[fd]) > 0:
                            try:
                                rc = self.fdmap[fd].send(self.outbuffmap[fd])
                                self.outbuffmap[fd] = self.outbuffmap[fd][rc:]
                                if len(self.outbuffmap[fd]) == 0:
                                    self.p.modify(fd, recv_mask)
                            except:
                                #raise
                                self.clean(fd)
                            continue

                    if event & recv_mask != 0:
                        try:
                            data = self.fdmap[fd].recv(BUF_SIZE)
                            recv_flag = True
                        except:
                            self.clean(fd)
                            continue
                        #except socket.error, serr:
                        #print("exception...")
                        #print(serr)
                        #self.clean(fd)
                    if not data and recv_flag:
                        try:
                            logging.debug("Closing connection from "+str(self.fdmap[fd].getpeername()))
                        except:
                            logging.debug("Closing connection " + str(fd))
                        self.clean(fd)
                    elif recv_flag:
                        logging.debug("LENGTH: " + str(len(data)))
                        self.buffmap[fd] += data
                        while(len(self.buffmap[fd]) > 3):
                            size = struct.unpack("!I", self.buffmap[fd][:4])[0]
                            if len(self.buffmap[fd]) >= size+4:
                                self.parse_request(self.buffmap[fd][4:size+4], fd)
                                if not fd in self.buffmap:
                                    break
                                self.buffmap[fd] = self.buffmap[fd][size+4:]
                            else:
                                break
            if self.kill_flag:
                sys.exit()
