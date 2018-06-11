#!/bin/env python

import os
import sys
import yaml
import signal
import time
import signal
import socket
from random import random
from argparse import RawTextHelpFormatter, \
                ArgumentParser

from threading import Timer, Thread

import node
from config import config_yaml, \
    threading_enabled, \
    _logger, \
    N, \
    RL


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


# def pbft_usage():
#     parser.add_argument("-n", "--nodes", dest="node_count", action='store',
#                         help="# of PBFT nodes to be launched")
#     parser.add_argument("-id", "--node-id", dest="node_id",
#                         action='store_true',
#                         help="")
#     parser.add_argument("-ts", "--tune-settings", dest="tune",
#                         action='store_true',
#                         help="")


if __name__ == "__main__":
    # import pdb; pdb.set_trace()
    print("Threading enabled: ", threading_enabled)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    def init_server(id):
        global RL
        try:
            ip, port = RL[id]
        except:
            quit("Ran out of replica list address range. No more server config to try")
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

    if threading_enabled:

        threads = []
        def run(ID):
            sys.stdout.write("run started\n")
            sys.stdout.flush()
            socket_obj = init_server(ID)
            n = node.node(ID, 0, N)
            # n.init_keys(N)
            n.init_replica_map(socket_obj)
            n.server_loop()
            sys.stdout.write("run exited\n")
            sys.stdout.flush()

        for i in range(N):
            thread = Thread(target=run, args=[i])
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        sys.stdout.write("join completed\n")
        sys.stdout.flush()

    else:
        # import pdb; pdb.set_trace()
        def init_server_socket(_id=None):
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

        socket_obj, _id = init_server_socket(
            _id=config_yaml["testbed_config"]["server_id_init"]-1
        )
        n = node.node(_id, 0, N)
        # n.init_keys(N)
        n.init_replica_map(socket_obj)
        n.server_loop()
