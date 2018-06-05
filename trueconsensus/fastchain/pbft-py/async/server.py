#!/usr/bin/python

import node
import config
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ID = int(sys.argv[1])
    else:
        ID = config.ID

    if len(sys.argv) > 2:
        n = node.node(ID, 0, config.N, int(sys.argv[2]))
    else:
        n = node.node(ID, 0, config.N)
    n.init_keys(10)
    n.init_replica_map()

    n.server_loop()
