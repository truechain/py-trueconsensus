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

from collections import OrderedDict, \
    namedtuple


class Node(object):
    '''
    @types:
    committee member
    committee non-member

    @state:
    corrup, honest(pre-corrupt, honest)

    '''
    def __init__(self, id=None, type=None):
        self.NodeId = id
        self._type = 'BFTmember'
        self.new_row = namedtuple('row', ['R','l','txn'])
        self.nonce = 0

    def log_to_snailchain(self):
        return
