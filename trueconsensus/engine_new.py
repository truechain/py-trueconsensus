#!/usr/bin/env python
#
# Copyright (c) 2018 TrueChain Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
# import yaml
import signal
import grpc
import struct
# import select
from datetime import datetime
import socket
# from random import random
from threading import Timer, active_count

from concurrent import futures

from trueconsensus.fastchain import node
from trueconsensus.fastchain.config import config_yaml, \
    THREADING_ENABLED, \
    CLIENT_ADDRESS, \
    _logger, \
    N, \
    RL

from trueconsensus.snailchain import SnailChain
from trueconsensus.fastchain.bft_committee import NodeBFT, \
    LedgerLog, \
    BFTcommittee

from trueconsensus.fastchain.subprotocol import SubProtoDailyBFT, \
    Mempools

from trueconsensus.proto import request_pb2, \
    request_pb2_grpc, \
    proto_message as message

from trueconsensus.utils.interruptable_thread import InterruptableThread

BUF_SIZE = 4096 * 8 * 8


def init_grpc_server(_id):
    global RL
    try:
        ip, port = RL[_id]
    except IndexError as E:
        quit("%s Ran out of replica list. No more server config to try" % E)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    request_pb2_grpc.add_FastChainServicer_to_server(FastChainServicer(), server)
    server.add_insecure_port('%s:%s' % (ip, port))
    server.start()
    msg = "Node: [%s], Msg: [Starting gRPC server], Address: [%s:%s]" % (_id, ip, port)
    print(msg)
    _logger.debug(msg)
    return server


countdown = 3 # time taken before node stops itself


def init_server(_id=None):
    """
    triggers setup using testbed_config. Increments given server id
    if that (ip, socket) from Replica List RL is already in use.
    """
    global N
    c = _id
    while c < N:
        s = None
        try:
            s = init_grpc_server(c)
        except OSError as E:
            _logger.error("%s -- Server ID: [%s]" % (E, c))
            c -= 1
        except Exception as E:
            _logger.error("%s -- Server ID: [%s]" % (E, c))
            c -= 1
        if s:
            return s, c

server, _id = init_server(
    _id=config_yaml["testbed_config"]["server_id_init"] - 1
)

n = node.Node(
    _id, 
    0, 
    N,
    max_requests=config_yaml['testbed_config']['requests']['max'],
    max_retries=config_yaml['testbed_config']['max_retries']
)


class FastChainServicer(request_pb2_grpc.FastChainServicer):
    # send_ack is exposed here
    def Send(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's outbuffmap and log this request
        return response
    
    def Check(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        # import pdb; pdb.set_trace()
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's log
        n.buffmap[request.inner.id].append(request)
        n.parse_request(request)
        return response

    def NewTxnRequest(self, request, context):
        # response = request_pb2.Transaction()
        # data = response.data
        # data.AccountNonce = request.data.AccountNonce
        # data.Price = request.data.Price
        # data.GasLimit = request.data.GasLimit
        # data.Recipient = request.data.Recipient
        # data.Amount = request.data.Amount
        # data.Payload = request.data.Payload

        response = request_pb2.GenericResp()
        response.msg = "received transaction"
        response.status = 200
        # TODO: Add txn to node's txnpool
        return response


def serve():
    # global server
    # global _id
    sys.stdout.write("run started\n")
    sys.stdout.flush()

    replica_status = n.init_replica_map(server)
    if not all(replica_status.values()):
        _logger.warn("Couldn't reach all replica in the list. Unreachable => {%s}" % 
            [i for i in replica_status if replica_status[i] is False])
    # grpc instance
    s = n.replica_map[n._id]
    _logger.info("Node: [%s], Current Primary: [%s]" % (n._id, n.primary))
    _logger.info("Node: [%s], Msg: [INIT SERVER LOOP]" % (n._id))
    # t = Timer(5, n.try_client)
    # t.start()

    while not self.is_stop_requested():
        data = None
        recv_flag = False
        _logger.debug("Node: [%s], Msg: [Got Connection], Address => {%s}" % (n._id, addr))
        n.buffmap[c.fileno()] = bytes()
        n.outbuffmap[c.fileno()] = bytes()
        n.connections += 1
        
        if event & send_mask != 0:
            if len(n.outbuffmap[fd]) > 0:
                try:
                    rc = n.fdmap[fd].send(n.outbuffmap[fd])
                    n.outbuffmap[fd] = n.outbuffmap[fd][rc:]
                    if len(n.outbuffmap[fd]) == 0:
                        n.p.modify(fd, recv_mask)
                except:
                    #raise
                    n.clean(fd)
                continue

        if event & recv_mask != 0:
            try:
                data = n.fdmap[fd].recv(BUF_SIZE)
                recv_flag = True
            except Exception as E:
                _logger.error("Node: [%s], Msg: [%s]" % (n._id, E))
                n.clean(fd)
                continue
            #self.clean(fd)
        if not data and recv_flag:
            try:
                peer_address = ":".join(str(i) for i in n.fdmap[fd].getpeername())
                _logger.debug("Node: [%s], Msg: [Close Connection], Event FileNum: [%s], Address: [%s]" % (n._id, fd, peer_address))
            except Exception as E:
                _logger.error("Node: [%s], Msg: [Close Connection], Event FileNum: [%s], ErrorMsg => {%s}" % (n._id, fd, E))
            n.clean(fd)
        elif recv_flag:
            _logger.debug("Node: [%s], ChunkLength: [%s]" % (n._id, len(data)))  # .decode('latin-1')))
            n.buffmap[fd] += data  # .decode('latin-1')
            while(len(n.buffmap[fd]) > 3):
                try:
                    size = struct.unpack("!I", n.buffmap[fd][:4])[0]
                except Exception as E:
                    _logger.error("Node: [%s], ErrorMsg => [%s]" % (n._id, E))
                    break
                    # import pdb; pdb.set_trace()

                if len(n.buffmap[fd]) >= size+4:
                    n.parse_request(n.buffmap[fd][4:size+4], fd)
                    if fd not in n.buffmap:
                        break
                    n.buffmap[fd] = n.buffmap[fd][size+4:]
                else:
                    # TODO: check if remaining buffmap of slice
                    # less than size+4 as leftover crumbs
                    break

    server.stop(0)
    # n.debug_print_bank()
    sys.stdout.write("run exited\n")
    sys.stdout.flush()
