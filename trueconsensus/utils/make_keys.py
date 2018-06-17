#!/bin/env python

# import sys

from trueconsensus.fastchain import ecdsa_sig as sig
from trueconsensus.fastchain.config import N


if __name__ == "__main__":
    print(sig.write_new_keys(N+1))
