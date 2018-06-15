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
from datetime import datetime
import socket
# from random import random
from argparse import RawTextHelpFormatter, \
                ArgumentParser

from threading import Timer, Thread

from fastchain import node
from fastchain.config import config_yaml, \
    threading_enabled, \
    _logger, \
    N, \
    RL

from snailchain import SnailChain
from fastchain.bft_committee import NodeBFT, \
    ViewChangeInit, \
    LedgerLog, \
    BFTcommittee

from fastchain.subprotocol import SubProtoDailyBFT, \
    Mempools

parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                        description="""PBFT standalone server demo""")


def suicide():
    # import pdb; pdb.set_trace()
    # sys.exit()
    # quit()
    os.kill(os.getpid(), signal.SIGINT)


def signal_handler(event, frame):
    sys.stdout.write("handling signal: %s\n" % event)
    sys.stdout.flush()
    _logger.error("Kill signal (%s) detected. Stopping pbft.." % event)
    countdown = 3  # seconds
    if event == signal.SIGINT:
        print("Committing deliberate suicide in %s seconds" % countdown)
        t = Timer(countdown, suicide)
        t.start()
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
    _logger.debug("Server [%s] -- listening on port %s" % (id, port))
    _logger.debug("IP: %s" % ip)
    return s


class ThreadedExecution(object):

    def __init__(self):
        pass

    def run(self, ID):
        sys.stdout.write("run started\n")
        sys.stdout.flush()
        socket_obj = init_server(ID)
        n = node.Node(ID, 0, N)
        # n.init_keys(N)
        n.init_replica_map(socket_obj)
        n.server_loop()
        sys.stdout.write("run exited\n")
        sys.stdout.flush()

    def launch(self):
        threads = []
        for i in range(N):
            thread = Thread(target=self.run, args=[i])
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        sys.stdout.write("join completed\n")
        sys.stdout.flush()


class NonThreadedExecution(object):
    '''
    Finds sockets that aren't busy and attempts to establish and launch testbed
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


# def pbft_usage():
#     parser.add_argument("-n", "--nodes", dest="node_count", action='store',
#                         help="# of PBFT nodes to be launched")
#     parser.add_argument("-id", "--node-id", dest="node_id",
#                         action='store_true',
#                         help="")
#     parser.add_argument("-ts", "--tune-settings", dest="tune",
#                         action='store_true',
#                         help="")


def main():
    print("Start time: ", datetime.now())
    print("Threading enabled: ", threading_enabled)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # import pdb; pdb.set_trace()
    if threading_enabled:
        ThreadedExecution().launch()
    else:
        NonThreadedExecution().launch()


if __name__ == "__main__":
    # import pdb; pdb.set_trace()
    main()
