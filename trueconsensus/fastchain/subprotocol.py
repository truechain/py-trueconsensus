#!/usr/bin/env python
#
# Copyright (c) 2018 TrueChain Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# import os
# import sys
import ecdsa
# from collections import defaultdict

from fastchain.ecdsa_sig import generate_keys
from fastchain.node import Node

# C = ecdsa.NIST256p
# SIG_SIZE = 64
# HASH_SIZE = 32


class Mempools(object):
    def __init__(self):
        self.txpool = []

    # def __repr__(self):
    #     return "Fork(mempool) --> snailpool"



class SubProtoDailyBFT(object):
    '''
    Subprotocol Daily BFT[R]
    '''

    def __init__(self, current_day=None):
        self.R = current_day
        self.l = 0
        self.log = []
        self.mykeys = []
        self.comm = []
        self.nodes = []
        self.TXs = []

    def keygen(self):
        """
        @pk public key
        @sk secret key
        """
        pk, sk = generate_keys()
        self.mykeys.append(pk)
        return pk

    def stop(self):
        # TODO: add signal / queue
        # for BFTpk in self.nodes:
        pass

    def start(self, comm):
        pass

    def forkVirtualNode(self):
        BFTpk = Node()


    def trigger(self, isMember=False):
        if isMember:
            for pk in set(self.mykeys) & set(self.comm):
                self.forkVirtualNode()
