#!/usr/bin/python

import os
import sys
import yaml
import signal
import time
import signal
import socket
import logging
from random import random
from argparse import RawTextHelpFormatter, \
                ArgumentParser

from threading import Timer, Thread

import node
from config import config_yaml, \
    threading_enabled, \
    N, \
    RL


parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                        description="""PBFT standalone server demo""")

# stop_requested = False


def suicide():
    # import pdb; pdb.set_trace()
    # quit("Committing suicide now")
    os.kill(os.getpid(), signal.SIGINT)


def signal_handler(event, frame):
    sys.stdout.write("handling signal: %s\n" % event)
    sys.stdout.flush()

    # global stop_requested
    # stop_requested = True

    print("\nKill signal (%s) detected. Stopping pbft.." % event)

    countdown = 3 # seconds
    print("Committing deliberate suicide in %s seconds" % countdown)
    if event == signal.SIGINT:
        t = Timer(countdown, suicide)
        t.start()
        sys.exit(130)  # Ctrl-C for bash


def pbft_usage():
    parser.add_argument("-n", "--nodes", dest="node_count", action='store',
                        help="# of PBFT nodes to be launched")
    parser.add_argument("-id", "--node-id", dest="node_id",
                        action='store_true',
                        help="Gather present satellite/capsule tunings")
    parser.add_argument("-ts", "--tune-settings", dest="tune",
                        action='store_true',
                        help="Tune as per performance recommendations")


# def simple_target(a):
#     print("hello - %s - %s" %(a, random()))

# def run(a):
#     sys.stdout.write("run started\n")
#     sys.stdout.flush()

#     while not stop_requested:
#         simple_target(a)
#         time.sleep(1)

#     sys.stdout.write("run exited\n")
#     sys.stdout.flush()

# key_dict = {}

# def init_keys(self, number):
#     global key_dict
#     for i in range(number):
#         key_dict[i] = sig.get_signing_key(i)


if __name__ == "__main__":
    # import pdb; pdb.set_trace()
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
        s.bind(('0.0.0.0', port))  # on EC2 we cannot directly bind on public addr
        s.listen(50)
        s.setblocking(0)
        print("Server " + str(id) + " listening on port " + str(port))
        print("IP: " + ip)
        return s

    if threading_enabled:

        threads = []
        def run(ID):
            sys.stdout.write("run started\n")
            sys.stdout.flush()

            # while not stop_requested:
            #     simple_target(a)
            #     time.sleep(1)

            socket_obj = init_server(ID)
            n = node.node(ID, 0, N)
            # n.init_keys(N)
            n.init_replica_map(socket_obj)
            n.server_loop()

            sys.stdout.write("run exited\n")
            sys.stdout.flush()

        # N = config_yaml['nodes']['total']
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
            attempts to loop over given ids to see if that (ip,socket)
            from replica list RL is already in use.
            """
            global N
            c = _id
            while c < N:
                s = None
                try:
                    s = init_server(c)
                except OSError as E:
                    # quit(E)
                    print(E, " -- Server ID: ", c)
                    c -= 1
                if s:
                    return s, c

        socket_obj, _id = init_server_socket(_id=config_yaml["nodes"]["server_id_init"]-1)
        n = node.node(_id, 0, N)
        # n.init_keys(N)
        n.init_replica_map(socket_obj)
        n.server_loop()
