#!/bin/env python

import socket
import os
import sys
import struct
import threading
import select
import time
import socks
# import time

from trueconsensus.dapps import bank
import proto_message as message
from trueconsensus.proto import request_pb2, request_pb2_grpc
from trueconsensus.fastchain.config import CLIENT_ADDRESS, \
    CLIENT_ID, \
    RL, \
    client_logger, \
    config_general
# N, TOR_SOCKSPORT

kill_flag = False
start_time = time.time()


def recv_response(n):
    global kill_flag
    count = 0
    print("RECEIVING")
    ClientReceiver

    client_logger.info("Client [%s] listening on port %s" % (CLIENT_ID, port))
    client_logger.info("Client IP: %s" % ip)
    p.register(s)
    # f = open("client_log.txt", 'w')
    client_msg = "[%s] SEQUENCE: 0 REPLICA: 0 START\n" % (time.time())
    # f.write(client_msg)
    client_logger.debug(client_msg)
    while(True):
        events = p.poll()
        client_logger.info("Current events queue: %s" % events)
        for fd, event in events:
            c, addr = s.accept()
            client_logger.debug("fd [%s] event [%s] addr [%s]" % (fd, event, addr))
            r = c.recv(4096)
            # size = struct.unpack("!I", r[:4])[0]
            req = request_pb2.Request()
            req.ParseFromString(r[4:])
            #print(req.inner.msg, req.inner.seq, "FROM", req.inner.id)
            client_msg = "[%s] SEQUENCE: %s - REPLICA: %s\n" % \
                (time.time(), req.inner.seq, req.inner.id)
            # f.write(client_msg)
            client_logger.info(client_msg)
            count += 1
            if req.inner.seq % 100 == 0:
            #if True:
                client_logger.debug("CLIENT [%s] SEQUENCE: %s" % (CLIENT_ID, req.inner.seq))
        #if req.inner.seq == n:
        if count == n * len(RL):
            kill_flag = True
            end_time = time.time()
            client_logger.debug('CLIENT [%s] total time spent with chain: %s' % (end_time - start_time))
            # f.close()


def send_requests():
    client_logger.info("Starting send for bufflen %s" % len(m))
    bank.gen_accounts(len(RL))
    start_time = time.time()
    # for i in range(n):
    RL_REQUEST_TRACKER = dict.fromkeys(["%s:%s" % (ip, port) for ip, port in RL], False)
    while not all_done:
        for ip, port in RL:
            try:
                # generate bank ids and add 1000 to every account
                # bank = bank.bank(id, 1000)
                # TODO: check if bi directional channel is needed
                channel = grpc.insecure_channel("%s:%s" % (ip, port))
                stub = request_pb2_grpc.Client(channel)
                new_txn = request_pb2.NewTxnRequest()
                new_txn.data = message.gen_txn(nonce, price, gas_limit, _to, fee, asset_bytes)
                
                # signify request being sent
                RL_REQUEST_TRACKER["%s:%s" % (ip, port)] = True
                if all(RL_REQUEST_TRACKER):
                    all_done = True

            except Exception as e:  # broad catch
                client_logger.error("Msg: [failed to send], Target: [%s:%s], Error => {%s}" % \
                                    (ip, port, e))
            

        m = m[size+4:]

    client_logger.info("Done sending... wait for receives")
    while True:
        time.sleep(1)
        if kill_flag:
            # give laggy requests some time to show up
            time.sleep(1)
            sys.exit()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        n = int(sys.argv[1])
    else:
        n = 50

    # id = 9
    # n = 0
    t = threading.Thread(target=recv_response, args=[n])
    t.daemon = True
    t.start()

    send_requests()