#!/usr/bin/env python
#
# fastchain.py: BFT committee codebase
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

import os
import uuid
import json
import random
import time

from trueconsensus.db.backends.level import LevelDB
from trueconsensus.fastchain import ecdsa_sig as sig
from trueconsensus.fastchain.log_maintainer import LedgerLog
from trueconsensus.fastchain.config import config_yaml, _logger
# from logging import ledger

from trueconsensus.fastchain.node import Node

from collections import OrderedDict, \
    defaultdict, \
    namedtuple  # for transaction tuple, use struct?

LAMBDA = config_yaml['bft_committee']['lambda']

# TODO: handle with protobuf / gRPC
GOSSIP_CONTEXT = {
    "VIEW_CHANGE": {
        "COMPLAIN": "replace_corrupt_node",
        "K_TIMEOUT": "replace_committee",
    },
    "DAILY_LOG": {
        "SIGN": "request_verify_log",
        "BATCHED": "dump_daily_log",
        "REQUEST_LOG": "fetch_entire_log",
    }
}


def generate_block(genesis=True):
    pass


def generate_txns(R, l):
    """
    Returns randomly generated tuple of txns with
    day R, l(seq of txn) and tx (hash id)
    """
    # uuid.uuid4().hex
    return (R, l, random.getrandbits(128))


# def genkey():
#     return uuid.uuid4().hex


class DailyOffChainConsensus(object):
    def __init__(self):
        self.chain = []
        self._lambda = None

    def preproess(self):
        pass


class NodeBFT(Node):
    '''
    '''
    R = 0
    LOGs = defaultdict(list)
    LOG = defaultdict()
    csize = LAMBDA
    state_map = []  # maps states of all nodes

    def __init__(self, id=None, type=None):
        self.NodeId = id
        self.isBFTNode = True
        self.new_row = namedtuple('row', ['R', 'l', 'txn'])
        # TODO: maybe use ctypes.Structure or struct.Struct ?
        self.nonce = 0

    @property
    def describe(self):
        return json.dumps({
            "R": self.R,
            "csize": self.csize,
            "BFT Member?": self.isBFTNode,
            "processing nonce?": self.nonce,
        })

    def __str__(self):
        return self.describe

    def launch_boot_nodes(self):
        return

    def log_to_snailchain(self):
        return


class BFTcommittee(object):
    '''
    member types:
    committee member
    committee non-member

    member states:
    corrup, honest(pre-corrupt, honest)
    '''

    def __init__(self, R, view, node_addresses):
        self.committee_id = R
        self.view = view
        self.nodes = node_addresses
        self.timeout = 300 # seconds? load from config
        self.timeout_viewchange = 300
        self.log = []

    @property
    def is_empty(self):
        if len(self.nodes) is 0:
            return True
        return False

    def handle_timeout(self, start, timeout_limit):
        current = time.time()
        if current - start >= timeout_limit:
            return True
        return False

    def wait_for_reply(self, start, context):
        gossiped = False
        while not gossiped:
            gossiped = self.gossip_to_snailchain(context)
            if self.handle_timeout(start, self.timeout_viewchange):
                return False            
        return True

    def call_to_viewchange(self, context):
        """
        complains to snailchain, init viewchange
        """
        start = time.time()
        response = None
        total = 0
        # TODO: derive timer logic from node.py
        # request_timer = Timer(self.timeout, self.handle_timeout, [req.dig, req.inner.view])
        # request_timer.daemon = True

        # TODO: handle timeout
        while True:
            response = self.wait_for_reply(start, context)
            # TODO: something like go routine to handle_timeout()
            if response is False:
                return False
            else:
                total = time.time() - start
                _logger.info("Total time taken for view change: %s" % total)
                return True
            if self.handle_timeout(start, self.timeout_viewchange):
                break
        return

    def sign_transaction(self, txn_tuple, from_node_id):
        """
        """
        key = sig.get_asymm_key(from_node_id, ktype="sign")
        signed_txn = sig.sign(key, txn_tuple)
        return signed_txn


    def log_to_slowchain(self):
        """
        """
        pass

    def fetch_LOG(self):
        """
        """
        pass

    def commit_txn(self):
        """
        """
        pass

    def genkey(self):
        """
        return (sk, vk) -> keypair generated by ECDSA
        """
        return sig.generate_keys()

    def sign_log(self, from_node_id):
        key = sig.get_asymm_key(from_node_id, ktype="sign")
        # TODO: handle conversation of log to bytes (use struct?)
        signed_log = sig.sign(key, self.log)
        return signed_log

    def append_to_log(self, txn_tuple):
        self.log.append(txn_tuple)

    def gossip_to_snailchain(self, context):
        """
        use UDP protocol / P2P to gossip to chain

        @context types:
            - VIEW_CHANGE - call for view change
        """
        pass

    def fork_vbft(self):
        pass

    def update_mempool_subprotocol(self):
        pass
