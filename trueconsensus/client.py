#!/bin/env python

# import proto_message as message
import socket
import os
import sys
import struct
import threading
import select
import time
import socks
# import time

from proto import request_pb2
from fastchain.config import client_address, \
    client_id, \
    RL, \
    client_logger, \
    config_general
# N, TOR_SOCKSPORT

kill_flag = False
start_time = 0


def recv_response(n):
    global kill_flag
    count = 0
    print("RECEIVING")
    s = socket.socket()
    p = select.epoll()
    ip, port = client_address
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(('0.0.0.0', port))
    s.listen(50)
    client_logger.info("Client [%s] listening on port %s" % (client_id, port))
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
                client_logger.debug("CLIENT [%s] SEQUENCE:" % (client_id, req.inner.seq))
        #if req.inner.seq == n:
        if count == n * len(RL):
            kill_flag = True
            client_logger.debug('CLIENT [%s] total time spent with chain: %s' % (end_time - start_time))
            # f.close()

if len(sys.argv) == 2:
    n = int(sys.argv[1])
else:
    n = 50

# id = 9
# n = 0
t = threading.Thread(target=recv_response, args=[n])
t.daemon = True
t.start()
requests_loc = os.path.join(
    config_general.get("node", "ledger_location"),
    "reqs.dat"
)
m = open(requests_loc, "rb").read()

client_logger.info("Loaded Messages")
client_logger.info("Starting send for bufflen %s" % len(m))
sock_list = []

# # import pdb; pdb.set_trace()
# for i in range(len(m)//4):
#     b = m[:4]
#     try:
#         # size is > 4 after unpacking the bytes
#         size = struct.unpack("!I", b)[0]
#     except struct.error:
#         # import pdb; pdb.set_trace()
#         break
#     m = m[size+4:]
#     # n += 1
#     # print(i, size, len(m))

start_time = time.time()
# for i in range(n):
while len(m) > 0:
    b = m[:4]
    try:
        size = struct.unpack("!I", b)[0]
    except struct.error:
        pass
    for ip, port in RL:
        try:
            #s = socket.socket()
            r = socks.socksocket()
            # r.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", TOR_SOCKSPORT[N], True)
            ## r.setblocking(0)
            r.connect((ip, port))
            # s.connect((ip,port))
            chunk = m[:size+4]
            client_logger.info("sending chunk of length %s over to replica set" % len(chunk))
            r.send(chunk)
            del chunk
            # s.send(m[:size+4])
            # sock_list.append(s)
            sock_list.append(r)
            r.close()
            # s.close()
        except Exception as e:  # broad catch
            client_logger.error("failed to send to [%s:%s] due to %s" % \
                                (ip, port, e))
            pass
    #s2 = socket.socket()
    #s2.connect(RL[0])
    #s2.send(m[:size+4])
    #s2.close()
    m = m[size+4:]

client_logger.info("Done sending... wait for receives")
while True:
    time.sleep(1)
    if kill_flag:
        # give laggy requests some time to show up
        time.sleep(1)
        sys.exit()
