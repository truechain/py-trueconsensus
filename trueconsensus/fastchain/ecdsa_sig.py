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

import sys
import os
import ecdsa
# import pickle
import config

C = ecdsa.NIST256p
SIG_SIZE = 64
HASH_SIZE = 32
FORMAT_MAP = {
    "verify": ".pem",
    "sign": ".pub"
}


def generate_keys():
    sk = ecdsa.SigningKey.generate(curve=C)
    vk = sk.get_verifying_key()
    return sk, vk


def sign(key, message):
    return key.sign(message)


# def verify(key, sig, message):
#     try:
#         rc = key.verify(sig, message)
#         return rc
#     except:
#         return False

def write_new_keys(n):
    if not os.path.isdir(config.KD):
        os.mkdir(config.KD)
    for i in range(0, n):
        s_file = open(format_kpath('sign', i), 'wb')
        v_file = open(format_kpath('verify', i), 'wb')
        sk, vk = generate_keys()
        s_file.write(sk.to_pem())
        v_file.write(vk.to_pem())
    s_file.close()
    v_file.close()


def get_signing_key(i):
    KP = format_kpath('sign', i)
    if not os.path.isfile(KP):
        print("can't find key file: ", KP)
        sys.exit(0)
    key_pem = open(KP, 'rb').read()
    return ecdsa.SigningKey.from_pem(key_pem)


def format_kpath(type, i):
    return os.path.join(
        config.KD,
        "{}{}{}".format(type, str(i), FORMAT_MAP[type])
    )


def get_verifying_key(i):
    KP = format_kpath('verify', i)
    if not os.path.isfile(KP):
        print("can't find key file: " + KP)
        sys.exit(0)
    key_pem = open(KP, 'rb').read()
    return ecdsa.VerifyingKey.from_pem(key_pem)


def read_keys_test(n, verify=True):
    if not os.path.isdir(config.KD):
        print("Can't find key directory")
        sys.exit(0)
    s = []  # signing / private key list
    v = []  # verifying / public key list
    for i in range(0, n):
        pem_key = open(format_kpath('sign', i), "rb").read()
        s.append(ecdsa.SigningKey.from_pem(pem_key))
        pub_key = open(format_kpath('verify', i), "rb").read()
        v.append(ecdsa.VerifyingKey.from_pem(pub_key))
        if verify:
            assert verify_pair(s[i], v[i], i) is True
    return s, v


def verify_pair(pem, pub, i):
    # sig_txt = ("message%s" % str(i)).encode(encoding="utf-8")
    sig_txt = bytes("message%s" % str(i), encoding="utf-8")
    sig = pem.sign(sig_txt)
    ver = pub.verify(sig, sig_txt)
    if not ver:
        print("erraneous round! check the key pair #" + str(i))
    else:
        print("Round " + str(i) + " succeeded")
        return True
    return False


if __name__ == "__main__":
    write_new_keys(10)
    read_keys_test(10, verify=False)
