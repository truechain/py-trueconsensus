from Crypto.Hash import SHA256
import struct

# import sig
from proto import request_pb2
from fastchain import ecdsa_sig as sig
from fastchain.config import _logger


def add_sig(key, id, seq, view, type, message, timestamp=None):
    """
    @key
    @id
    @seq
    @view
    @type
    @message
    @timestamp
    """
    #key = sig.get_signing_key(id)
    req = request_pb2.Request()
    inner = req.inner
    inner.id = id
    inner.seq = seq
    inner.view = view
    inner.type = type
    inner.msg = message
    if timestamp:
        inner.timestamp = timestamp
    #req.inner = inner
    b = inner.SerializeToString()
    h = SHA256.new()
    h.update(b)
    digest = h.digest()
    s = sig.sign_proto_key(key, digest)
    req.dig = digest
    req.sig = s
    return req

def check(key, req):
    id = req.inner.id
    #key = sig.get_signing_key(id)

    digest_recv = req.dig
    sig_recv = req.sig
    msg = req.inner.msg

    i = req.inner.SerializeToString()
    h = SHA256.new()
    h.update(i)
    digest = h.digest()
    _logger.debug("check(%s) against (%s)" % (key, req))
    s = (sig.verify_proto_key(key, sig_recv, digest_recv) and digest == digest_recv)
    if s:
        return req
    else:
        return None
    return req

'''def check(req):
    #req = request_pb2.Request()
    #req.ParseFromString(message)
    id = req.inner.id
    key = sig.get_verifying_key(id)

    digest_recv = req.dig
    signature = req.sig
    msg = req.inner.msg

    h = SHA256.new()
    h.update(req.inner.SerializeToString())
    digest = h.digest()

    s = (sig.verify(key, signature, digest_recv) and digest == digest_recv)
    if s:
        return req
    else:
        return None

'''
