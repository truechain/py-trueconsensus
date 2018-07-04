#!/bin/env python

import os
import sys
import grpc
import struct
import select
import time

from trueconsensus.dapps.bank import Bank, Users
from trueconsensus.proto import request_pb2, \
    request_pb2_grpc, \
    proto_message as message
from trueconsensus.fastchain.config import CLIENT_ADDRESS, \
    CLIENT_ID, \
    RL, \
    N, \
    client_logger, \
    config_general, \
    config_yaml

kill_flag = False
start_time = time.time()
GRPC_REQUEST_TIMEOUT = config_yaml["grpc"]["timeout"]

def send_ack(_id):
    # TODO: verifications/checks
    return 200

class ClientReceiverServicer(request_pb2_grpc.ClientReceiverServicer):
    def PbftReplyReceiver(self, request, context):
        response = request_pb2.PbftBlock()
        stamp_to_chain(request)
        return response

    def Check(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        response.status = send_ack(request.inner.id)
        stamp_to_chain(request, test_connection=True)
        return response


def stamp_to_chain(req, test_connection=False):
    client_msg = "[%s] SEQUENCE: 0 REPLICA: 0 START\n" % (time.time())
    # f.write(client_msg)
    client_logger.debug(client_msg)
    import pdb; pdb.set_trace()
    client_msg = "[%s] SEQUENCE: %s - REPLICA: %s\n" % \
        (time.time(), req.inner.seq, req.inner.id)
    # f.write(client_msg)
    client_logger.info(client_msg)
    count += 1
    if req.inner.seq % 100 == 0:
    #if True:
        client_logger.debug("CLIENT [%s] SEQUENCE: %s" % (CLIENT_ID, req.inner.seq))
    #if req.inner.seq == n:
    if count == N * len(RL):
        kill_flag = True
        end_time = time.time()
        client_logger.debug('CLIENT [%s] total time spent with chain: %s' % (end_time - start_time))
        # f.close()


def gen_requests():
    client_key_pub = ecdsa_sig.get_asymm_key(CLIENT_ID-1, ktype='verify')
    client_key_pem = ecdsa_sig.get_asymm_key(CLIENT_ID-1, ktype='sign')
    keys_to_seq_tracker = defaultdict.fromkeys(range(N), 0)
    
def send_requests(all_done=False):
    UserTap = Users()
    UserTap.open_db_conn()
    UserTap.gen_accounts(len(RL))
    start_time = time.time()
    RL_REQUEST_TRACKER = dict.fromkeys(range(N), False)
     
    while not all_done:
        for target_node in range(N):
            if target_node == CLIENT_ID:
                continue
            try:
                # generate bank ids and add 1000 to every account
                # bank = bank.bank(id, 1000)
                # TODO: check if bi directional channel is needed
                
                channel = grpc.insecure_channel("%s:%s" % RL[target_node])
                stub = request_pb2_grpc.FastChainStub(channel)
                new_txn = request_pb2.Transaction()
                # nonce, price, gas_limit, _to, fee, asset_bytes
                new_txn.dest = target_node
                new_txn.source = CLIENT_ID
                message.gen_txn_data(new_txn.data)
                response = stub.NewTxnRequest(new_txn, timeout=GRPC_REQUEST_TIMEOUT)
                # signify request being sent
                RL_REQUEST_TRACKER[target_node] = True
            except Exception as e:  # broad catch
                import pdb; pdb.set_trace()
                client_logger.error("Msg: [failed to send], Target: [%s:%s], Error => {%s}" % \
                                    (*RL[target_node], e))
        if all(RL_REQUEST_TRACKER.values()):
            all_done = True

        time.sleep(1)            

    client_logger.info("Done sending... wait for receives")
    UserTap.close_db_conn()
    while True:
        time.sleep(1)
        if kill_flag:
            # give laggy requests some time to show up
            time.sleep(1)
            sys.exit()

if __name__ == '__main__':
    try:
        if len(sys.argv) == 2:
            n = int(sys.argv[1])
        else:
            n = 50
        send_requests()
    except KeyboardInterrupt:
        quit("Ctrl-C'ed. Exiting..")