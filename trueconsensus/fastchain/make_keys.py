#!/bin/env python

# import sys

import ecdsa_sig as sig
from config import N


if __name__ == "__main__":
    sig.write_new_keys(N+1)
