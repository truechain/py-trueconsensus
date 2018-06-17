### Errors

Collection of sommon common errors while coding, for troubleshooting:


#### byte-like objects or str required

1. `TypeError: a bytes-like object is required, not 'str'`

```
TypeError: a bytes-like object is required, not 'str'
DEBUG:trueconsensus_engine.log:--> Trying client ('127.0.0.1..
```

Your log file write mode was `wb` instead of `w`.


2. `TypeError: key: expected bytes or bytearray, but got 'SigningKey'`

```
 File "/home/arcolife/workspace/projects/Truechain/forked/py-trueconsensus/trueconsensus/fastchain/pbft-py/node.py", line 878, in parse_request
    req = message.check(key,req)
  File "/home/arcolife/workspace/projects/Truechain/forked/py-trueconsensus/trueconsensus/fastchain/pbft-py/proto_message.py", line 40, in check
    s = (sig.verify(key, sig_recv, digest_recv) and digest == digest_recv)
  File "/home/arcolife/workspace/projects/Truechain/forked/py-trueconsensus/trueconsensus/fastchain/pbft-py/sig.py", line 25, in verify
    h = hmac.new(key, bytes, hashlib.sha256)
  File "/home/arcolife/workspace/projects/Truechain/forked/py-trueconsensus/trueconsensus/fastchain/pbft-py/venv/lib64/python3.6/hmac.py", line 144, in new
    return HMAC(key, msg, digestmod)
  File "/home/arcolife/workspace/projects/Truechain/forked/py-trueconsensus/trueconsensus/fastchain/pbft-py/venv/lib64/python3.6/hmac.py", line 42, in __init__
    raise TypeError("key: expected bytes or bytearray, but got %r" % type(key).__name__)
TypeError: key: expected bytes or bytearray, but got 'SigningKey'
DEBUG:trueconsensus_engine.log:--> Trying client ('127.0.0.1', 49504) from server ID: 3 
```

Make the following changes:

```
key = bytes(key.to_string())
h = hmac.new(key, message, hashlib.sha256)
```

3. 