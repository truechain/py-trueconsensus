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
import struct
import select
from datetime import datetime
import socket
# from random import random
from threading import Timer, active_count

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

from trueconsensus.utils.interruptable_thread import InterruptableThread


BUF_SIZE = 4096 * 8 * 8
recv_mask = select.EPOLLIN | select.EPOLLPRI | select.EPOLLRDNORM
send_mask = select.EPOLLOUT | select.EPOLLWRNORM

# class GracefulExit(object):
#     def __enter__(self):
#         # set up signals here
#         # store old signal handlers as instance variables

#     def __exit__(self, type, value, traceback):
#         # restore old signal handlers

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


def init_server(id):
    global RL
    try:
        ip, port = RL[id]
    except IndexError as E:
        quit("%s Ran out of replica list. No more server config to try" % E)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # host = socket.gethostname()
    host = "0.0.0.0"
    s.bind((host, port))  # on EC2 we cannot directly bind on public addr
    s.listen(50)
    s.setblocking(0)
    msg = "Server [%s] IP [%s] -- listening on port %s" % (id, ip, port)
    print(msg)
    _logger.debug(msg)
    return s

            
class ThreadedExecution(InterruptableThread):
    '''
    Launches test nodes as threads
    '''
    def __init__(self, _id):
        self._id = _id
        self.countdown = 3 # time taken before node stops itself
        InterruptableThread.__init__(self)


    # def try_client(self):
    #     ip, port = CLIENT_ADDRESS
    #     _logger.debug("Node: [%s], Msg: [Trying client], Target: [%s]" % \
    #                   (self._id, CLIENT_ADDRESS))
    #     while not self.is_stop_requested():
    #         # time.sleep(5)
    #         self.clientlock.acquire()
    #         if len(self.clientbuff) > 0:
    #             try:
    #                 self.send_to_client(self.clientbuff)
    #                 self.clientbuff = bytes()
    #             except Exception as E:
    #                 _logger.error("Node: [%s], ErrorMsg => {while trying client, encountered: %s}" % (self._id, E))
    #         self.clientlock.release()


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

        socket_obj = init_server(self._id)
        n = node.Node(
            self._id, 
            0, 
            N, 
            max_requests=config_yaml['testbed_config']['requests']['max']
        )

        n.init_replica_map(socket_obj)

        # counter = 0
        # self.fdmap[s.fileno] = s
        # self.p.register(s, recv_mask)
        s = n.replica_map[n._id]

        _logger.info("Node: [%s], Current Primary: [%s]" % (n._id, n.primary))
        _logger.info("Node: [%s], Msg: [INIT SERVER LOOP]" % (n._id))
        

        t = Timer(5, n.try_client)
        t.start()

        while not self.is_stop_requested():
            events = n.p.poll()
            _logger.debug("Node: [%s], Msg: [Polling Queue], Events => {%s}" % (n._id, events))
            for fd, event in events:
                # counter += 1
                # need the flag for "Service temporarilly unavailable" exception
                data = None
                recv_flag = False
                if fd is s.fileno():
                    c, addr = s.accept()
                    _logger.debug("Node: [%s], Msg: [Got Connection], Address => {%s}" % (n._id, addr))
                    #print("Got connection from " + str(addr))
                    c.setblocking(0)
                    #c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
                    n.p.register(c, recv_mask)
                    n.fdmap[c.fileno()] = c
                    n.buffmap[c.fileno()] = bytes()
                    n.outbuffmap[c.fileno()] = bytes()
                    n.connections += 1
                else:
                    # if we have a write event
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
                        #except socket.error, serr:
                        #print("exception...")
                        #print(serr)
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
                s = init_server(c)
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
    main()
