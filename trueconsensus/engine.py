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
import time
# import select
from datetime import datetime
import socket
# from random import random
from threading import Timer, active_count

from concurrent import futures

from trueconsensus.fastchain import node, record_pbft
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
node_instances = {}
NODE_ID = None

# recv_mask = select.EPOLLIN | select.EPOLLPRI | select.EPOLLRDNORM
# send_mask = select.EPOLLOUT | select.EPOLLWRNORM

# class GracefulExit(object):
#     def __enter__(self):
#         # set up signals here
#         # store old signal handlers as instance variables

#     def __exit__(self, type, value, traceback):
#         # restore old signal handlers

def send_ack(_id):
    # TODO: verifications/checks
    return 200

class FastChainServicer(request_pb2_grpc.FastChainServicer):
    # send_ack is exposed here
    def Send(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        response.status = send_ack(request.inner.id)
        NODE_ID = request.dest
        # print("%s => %s" % (_id, NODE_ID))
        n = node_instances[NODE_ID] # NODE_ID is server's ID, that invoked its Check() with RPC 
        n.incoming_buffer_map[_id].append(request)
        n.parse_request(request)
        # TODO: add request to node's outbuffmap and log this request
        return response
    
    def Check(self, request, context):
        global node_instances
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        # import pdb; pdb.set_trace()
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's log
        _id = request.inner.id # id of server that sent the request (from)
        NODE_ID = request.dest
        # print("%s => %s" % (_id, NODE_ID))
        n = node_instances[NODE_ID] # NODE_ID is server's ID, that invoked its Check() with RPC 
        n.incoming_buffer_map[_id].append(request)
        n.parse_request(request)
        return response

    def NewTxnRequest(self, request, context):
        # actually receive data
        # recv_flag = True
        # except Exception as E:
        #     _logger.error("Node: [%s], Msg: [%s]" % (n._id, E))
        #     n.clean(fd)
        response = request_pb2.GenericResp()
        NODE_ID = request.dest

        # TODO:
        # empty data -> close conn / check if applicable, 
        # now that we have gRPC instead of socket
        # import pdb; pdb.set_trace()
        if not request.data:  # and recv_flag:
            # print("%s => %s" % (_id, NODE_ID))
            _logger.debug("Node: [%s], Msg: [Received Empty Data in Transaction]" % (NODE_ID))
            # n.clean(NODE_ID)
            response.msg = "No Content"
            response.status = 204
        else:
            n = node_instances[NODE_ID] # NODE_ID is server's ID, that invoked its Check() with RPC 
            # TODO: segregate into receiever
            # finally got data on receval
            # _logger.debug("Node: [%s], ChunkLength: [%s]" % (NODE_ID, len(data)))
            n.txpool.append(request.data)
            response.msg = "received transaction"
            response.status = 200
        _logger.debug("Node: [%s], Msg: [Received Client Request for Acc Nonce %s for Recipient %s]" % 
            (NODE_ID, request.data.AccountNonce, request.data.Recipient))        
        # TODO: Add txn to node's txnpool, regardless of bad request. Keep track
        return response
        

def suicide():
    # import pdb; pdb.set_trace()
    # sys.exit()
    # quit()
    print("Active Thread Count: ", active_count())
    os.kill(os.getpid(), signal.SIGINT)

def signal_handler(event, frame):
    sys.stdout.write("handling signal: %s\n" % event)
    sys.stdout.flush()
    _logger.error("Kill signal (%s) detected. Stopping pbft.." % event)
    countdown = 3  # seconds
    if event == signal.SIGINT:
        print("Committing deliberate suicide in %s seconds" % countdown)
        print("Active Thread Count: ", active_count())
        t = Timer(countdown, suicide)
        print("End time: ", datetime.now())
        t.start()
        print("Active Thread Count: ", active_count())
        sys.exit(130)  # Ctrl-C for bash

def init_grpc_server(_id):
    global RL
    # import pdb; pdb.set_trace()
    try:
        ip, port = RL[_id]
    except IndexError as E:
        quit("%s Ran out of replica list. No more server config to try" % E)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    request_pb2_grpc.add_FastChainServicer_to_server(FastChainServicer(), server)
    server.add_insecure_port('%s:%s' % (ip, port))
    server.start()
    msg = "Node: [%s], Msg: [Firing up gRPC channel], Address: [%s:%s]" % (_id, ip, port)
    print(msg)
    _logger.debug(msg)
    return server

            
class ThreadedExecution(InterruptableThread):
    '''
    Launches test nodes as threads
    '''
    def __init__(self, _id):
        self._id = _id
        self.countdown = 3 # time taken before node stops itself
        InterruptableThread.__init__(self)

    # def server_loop(self):
    def run(self):
        """
        call flow graph:

        -> server_loop() -> parse_request() ->
        self.request_types[req.inner.type]() -> [] process_client_request() ->
        execute_in_order() -> execute() ->
            - self.bank.process_request()
            - client_sock.send()
            - record()
        -> suicide() when Max Requests reached..
        """        
        sys.stdout.write("run started\n")
        sys.stdout.flush()

        n = node.Node(
            self._id, 
            0, 
            N, 
            max_requests=config_yaml['testbed_config']['requests']['max'],
            max_retries=config_yaml['testbed_config']['max_retries']
        )

        global node_instances
        node_instances[self._id] = n

        global NODE_ID 
        NODE_ID = self._id

        self.server = init_grpc_server(self._id)

        replica_status = n.init_replica_map(self.server)
        # import pdb; pdb.set_trace()
        if not all(replica_status.values()):
            _logger.warn("Couldn't reach all replica in the list. Unreachable => {%s}" % 
                [i for i in replica_status if replica_status[i] is False])
        # grpc instance
        s = n.replica_map[n._id]
        _logger.info("Node: [%s], Current Primary: [%s]" % (n._id, n.primary))
        msg = "Node: [%s], Msg: [INIT SERVER LOOP]" % (n._id)
        print(msg)
        _logger.info(msg)
        # t = Timer(5, n.try_client)
        # t.start()

        while not self.is_stop_requested():
            # trigger events based on flags ?
            data = None

            for target_node in range(N):
                if target_node == self._id:
                    continue

                # send data
                # TODO: send this reply to all slowchain members
                if len(n.outgoing_buffer_map[target_node]) > 0:
                    try:
                        # TODO: integrate with config_yaml["bft_committee"]["block_frequency"]
                        response = n.send_reply_to_client(target_node)
                        n.outgoing_buffer_map[target_node].pop(-1)
                        _logger.info("Node: [%s], Msg: [Block sent to client], Status: [%d], Response: [%s]"
                            % (n._id, response.status, response.value))
                        # new_txn = request_pb2.NewTxnRequest()
                        # new_txn.data = message.gen_txn(nonce, price, gas_limit, _to, fee, asset_bytes)
                    except IndexError:
                        pass
                    except:
                        #raise
                        n.clean(target_node)

                # process outmap /inmap in the same loop?
                while(len(n.incoming_buffer_map[target_node]) > config_yaml["bft_committee"]["block_size"]):
                    # TODO: parse_request() could actually read from incoming requests
                    # but maybe we might not wanna handle it this way
                    n.parse_request(n.incoming_buffer_map[target_node][-1])
                    n.incoming_buffer_map[target_node].pop(-1)

            time.sleep(4)
            _logger.debug("Node: [%s], Waiting for next batch.." % (n._id))

        self.server.stop(0)
        # n.debug_print_bank()
        sys.stdout.write("run exited\n")
        sys.stdout.flush()


class NonThreadedExecution(object):
    '''
    Finds sockets that aren't busy and attempts to establish and 
    launches test nodes as individual processes
    '''
    def __init__(self):
        pass

    def init_server_socket(self, _id=None):
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
            if s:
                return s, c

    def launch(self):
        socket_obj, _id = self.init_server_socket(
            _id=config_yaml["testbed_config"]["server_id_init"] - 1
        )
        n = node.Node(_id, 0, N)
        # n.init_keys(N)
        n.init_replica_map(socket_obj)
        n.server_loop()


def main():
    print("Start time: ", datetime.now())
    print("Threading enabled: ", THREADING_ENABLED)

    # signal.signal(signal.SIGINT, self.debug_print_bank)

    # with GracefulExit():
    #     pass
    
    # import pdb; pdb.set_trace()
    if THREADING_ENABLED:
        
        thread_pool = []
        
        for _id in range(N):
            # sys.stdout.write("Active Thread Count: ", active_count())
            node_instance = ThreadedExecution(_id)
            node_instance.start()
            thread_pool.append(node_instance)

        for thread in thread_pool:
            thread.join()
        
        sys.stdout.write("all exited\n")
        sys.stdout.flush()
    else:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        NonThreadedExecution().launch()

    print("End time: ", datetime.now())


if __name__ == "__main__":
    # import pdb; pdb.set_trace()
    try:
        main()
    except KeyboardInterrupt:
        quit("Ctrl-C'ed. Exiting..")

