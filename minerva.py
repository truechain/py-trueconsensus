#!/bin/env python

import sys
from argparse import RawTextHelpFormatter, \
                ArgumentParser

from trueconsensus import engine

parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                        description="""Hybrid BFT based consensus - standalone engine""")

def consensus_usage():
    parser.add_argument("-n", "--nodes", dest="node_count", action='store',
                        help="# of PBFT nodes to be launched")
    parser.add_argument("-c", "--conf", dest="node_id",
                        action='store_true',
                        help="")
    parser.add_argument("-ts", "--tune-settings", dest="tune",
                        action='store_true',
                        help="")

if __name__ == '__main__':
    engine.main()
