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

"""
Relative package import structure 
"""

import os

try:
    # If a VERSION file exists, use it!
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(version_file) as fh:
        __version__ = fh.read().strip()
except NameError:
    __version__ = 'unknown (running code interactively?)'
except IOError, ex:
    __version__ = "unknown (%s)" % ex


###########################################################
# PACKAGES
###########################################################

from snailchain import *
from fastchain import *

# explicitly import all top-level modules (ensuring
# they override the same names inadvertently imported
# from a subpackage)

import snailchain, fastchain
