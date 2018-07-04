#!/bin/env python

import sys
from argparse import RawTextHelpFormatter, \
                ArgumentParser


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
    try:
        from trueconsensus import engine
        engine.main()
        # from trueconsensus import engine_new
        # engine_new.serve()
    except KeyboardInterrupt:
        sys.exit(1)