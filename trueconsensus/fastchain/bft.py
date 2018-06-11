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
import random
from db.backends.level import LevelDB

# from logging import ledger

from fastchain.node import Node
from collections import OrderedDict, \
    defaultdict, \
    namedtuple


global LAMBDA
LAMBDA = 0


def generate_block(genesis=True):
    pass


def generate_txns(R, l):
    """
    Returns randomly generated tuple of txns with
    day R, l(seq of txn) and tx (hash id)
    """
    return (R, l, random.getrandbits(128))
    uuid.uuid4().hex


# def genkey():
#     return uuid.uuid4().hex


class NodeBFT(Node):
    '''
    @types:
    committee member
    committee non-member

    @state:
    corrup, honest(pre-corrupt, honest)

    '''
    R = 0
    LOGs = defaultdict(list)
    LOG = defaultdict()
    csize = LAMBDA

    def __init__(self, id=None, type=None):
        self.NodeId = id
        self._type = 'BFTmember'
        self.new_row = namedtuple('row', ['R','l','txn'])
        self.nonce = 0

    def log_to_snailchain(self):
        return


class ViewChangeInit(object):
    '''
    '''

    def __init__(self):
        pass


class LedgerLog(object):
    def __init__(self):
        pass

class BFTcommittee(object):
    '''
    '''

    def __init__(self):
        self.nodes = []
        self.view = 0

    def call_to_viewchange(self):
        """
        complains to snailchain
        """
        self.ViewChangeInit(self.nodes)

    def sign_transaction(self):
        """
        """
        pass

    def log_to_slowchain(self):
        """
        """
        pass

    def fetch_LOG(self):
        """
        """
        pass
