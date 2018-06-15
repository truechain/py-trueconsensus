#!/bin/env python

# import sys

from fastchain import ecdsa_sig as sig
from fastchain.config import N


if __name__ == "__main__":
    print(sig.write_new_keys(N+1))
