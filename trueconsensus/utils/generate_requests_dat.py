#!/bin/env python

import os
import sys
import socket
import random
import struct
import sqlite3
from collections import defaultdict


# import sig
from trueconsensus.fastchain import ecdsa_sig
from trueconsensus.fastchain.config import CLIENT_ID, \
    config_yaml, \
    config_general, \
    N
# import request_pb2
import trueconsensus.proto.proto_message as message


def backspace(n):
    # print((b'\x08' * n).decode(), end='') # use \x08 char to go back
    x = '\r' * n
    print(x, end="", flush=True)            # use '\r' to go back


def gen_requests(max_requests, batch_size, f):
    client_key_pub = ecdsa_sig.get_asymm_key(CLIENT_ID-1, ktype='verify')
    client_key_pem = ecdsa_sig.get_asymm_key(CLIENT_ID-1, ktype='sign')
    keys_to_seq_tracker = defaultdict.fromkeys(range(N), 0)
    for i in range(max_requests):
        # print("for request: [%s]" % i)
        r = random.randint(1, max_requests)
        r2 = random.randint(max_requests/2, max_requests)
        # amount = random.randint(0,100)
        amount = 50
        msg = "TRAN%s%s" % (
            str(amount).zfill(4),
            str(r2).zfill(4),
            #.decode('latin1')
        )
        msg = bytes(msg, encoding="utf-8") + client_key_pub.to_string()
        if i == 0:
            print(len(client_key_pub.to_string()), "ECDSA")
        
        _id = r%N
        # print("current ID: ", _id)
        current_key = ecdsa_sig.get_asymm_key(_id, ktype='sign')
        # import pdb; pdb.set_trace()
        seq = keys_to_seq_tracker[_id]
        view = 0 # TODO: do we even need view in request from client??
        req = message.add_sig(current_key, _id, seq, view, "REQU", msg, i)
        keys_to_seq_tracker[_id] += 1  # Increase seq count since same node might send another request
        req.sig = client_key_pem.to_string()
        msg = req.SerializeToString()
        if i == 0:
            print("one request:", len(msg))
        ################################
        #padding = "0123456789" * 10
        #msg += padding * 1024
        #msg += "x" * (400 - len(msg))
        msg += msg * (batch_size-1)
        ################################
        temp = message.add_sig(current_key, _id, 0, 0, "REQU", msg, i+offset)
        size = temp.ByteSize()
        if i == 0:
            print("inner message:", len(msg))
            print("message byte size:", size)
        b = struct.pack("!I", size)
        f.write(b+temp.SerializeToString())
        # if i % batch_size == 0:
        s = "Generation Progress: {:.1%}".format(i/max_requests)
        print(s, end='')
        backspace(len(s))
        # time.sleep(0.02)
    # see the counter
    print("keys_to_seq_tracker: ", keys_to_seq_tracker)

if __name__ == '__main__':
    max_requests = config_yaml["testbed_config"]["requests"]["max"]
    batch_size = config_yaml["testbed_config"]["requests"]["batch_size"]
    assert batch_size < max_requests

    print("Generating [%s] requests with batch size [%s]" %
          (max_requests, batch_size))
    offset = random.randint(0, 99999999)  # 0
    print("Offset:", offset)

    requests_loc = os.path.join(
        config_general.get("node", "ledger_location"),
        "reqs.dat"
    )
    f = open(requests_loc, "wb")
    gen_requests(max_requests, batch_size, f)
    f.close()
    print("Finished Message Generation")
