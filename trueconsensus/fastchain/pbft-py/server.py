#!/usr/bin/python

import os
import sys
import yaml
import signal
import time
import signal
import logging
from random import random
from argparse import RawTextHelpFormatter, \
                ArgumentParser

import node
from config import config_yaml, \
    threading_enabled, \
    N


parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                        description="""PBFT standalone server demo""")

stop_requested = False


def signal_handler(event, frame):
    sys.stdout.write("handling signal: %s\n" % event)
    sys.stdout.flush()

    global stop_requested
    stop_requested = True

    print("\nKill signal (%s) detected. Stopping pbft.." % event)
    if event == signal.SIGINT:
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
    
    if threading_enabled:
        from threading import Thread

        threads = []
        def run(ID):
            sys.stdout.write("run started\n")
            sys.stdout.flush()

            # while not stop_requested:
            #     simple_target(a)
            #     time.sleep(1)

            n = node.node(ID, 0, N)
            # n.init_keys(N)
            n.init_replica_map()
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
        n = node.node(0, 0, N)
        # n.init_keys(N)
        n.init_replica_map()
        n.server_loop()
