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

import os
# from subprocess import check_output

MAX_FAIL = 1
N = 2  # the number of parties excluding the client
basePort = 49505

host_file_content = open(os.path.expanduser('~')+'/hosts', 'r').read()
IP_LIST = [l.strip() for l in host_file_content.split('\n') if l]
total = len(IP_LIST)

# We reserve the last IP as the client
RL = [(l, basePort+i) for i, l in enumerate(IP_LIST[:N])]

TOR_SOCKSPORT = range(9050, 9150)

ID = 0  # Now ID is deprecated
N = len(RL)

client = ((IP_LIST[N], basePort+N))

# KEY DIRECTORY
KD = os.getcwd() + "/keys"
print(KD)
