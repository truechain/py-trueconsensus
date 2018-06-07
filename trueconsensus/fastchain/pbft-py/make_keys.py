# import sys

import ecdsa_sig as sig
from config import config_yaml


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print "USAGE"
    #     sys.exit(0)
    N = config_yaml['nodes']['total']
    # sig.write_new_keys(int(sys.argv[1]))
    sig.write_new_keys(N)
