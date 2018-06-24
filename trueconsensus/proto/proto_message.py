from Crypto.Hash import SHA256
import struct

# import sig
from trueconsensus.proto import request_pb2, request_pb2_grpc
from trueconsensus.fastchain import ecdsa_sig as sig
from trueconsensus.fastchain.config import _logger

def gen_txn(nonce, price, gas_limit, _to, fee, asset_bytes):
    """
    """
    txn = request_pb2.TxnData()
    txn.data.AccountNonce = nonce
    txn.data.Price = price
    txn.data.GasLimit = gas_limit
    txn.data.Recipient = _to
    txn.data.Amount = fee
    txn.data.Payload = asset_bytes
    return txn


def add_sig(key, _id, seq, view, req_type, message, timestamp=None):
    """
    @key
    @_id
    @seq
    @view
    @req_type
    @message
    @timestamp
    """
    #key = sig.get_signing_key(id)
    req = request_pb2.Request()
    inner = req.inner
    inner.id = _id
    inner.seq = seq
    inner.view = view
    inner.type = req_type
    # block = inner.block
    if timestamp:
        inner.timestamp = timestamp
    #req.inner = inner
    b = inner.SerializeToString()
    h = SHA256.new()
    h.update(b)
    digest = h.digest()
    # import pdb; pdb.set_trace()
    s = sig.sign_proto_key(key, digest)
    msg_sig = req.sig
    req.dig = digest
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
    # _logger.debug("check(%s) against (%s)" % (key, req))
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


def send_ack(_id):
    # TODO: verifications/checks
    return 200


class FastChainServicer(request_pb2_grpc.FastChainServicer):
    # send_ack is exposed here
    def Send(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's outbuffmap and log this request
        return response
    
    def Check(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        # import pdb; pdb.set_trace()
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's log
        return response

    def NewTxnRequest(self, request, context):
        # response = request_pb2.Transaction()
        # data = response.data
        # data.AccountNonce = request.data.AccountNonce
        # data.Price = request.data.Price
        # data.GasLimit = request.data.GasLimit
        # data.Recipient = request.data.Recipient
        # data.Amount = request.data.Amount
        # data.Payload = request.data.Payload

        response = request_pb2.GenericResp()
        response.msg = "received transaction"
        response.status = 200
        # TODO: Add txn to node's txnpool
        return response


class FastChainServicer(request_pb2_grpc.FastChainServicer):
    # send_ack is exposed here
    def Send(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's outbuffmap and log this request
        return response
    
    def Check(self, request, context):
        response = request_pb2.GenericResp()
        response.msg = request.inner.type
        # import pdb; pdb.set_trace()
        response.status = send_ack(request.inner.id)
        # TODO: add request to node's log
        return response

    def NewTxnRequest(self, request, context):
        # response = request_pb2.Transaction()
        # data = response.data
        # data.AccountNonce = request.data.AccountNonce
        # data.Price = request.data.Price
        # data.GasLimit = request.data.GasLimit
        # data.Recipient = request.data.Recipient
        # data.Amount = request.data.Amount
        # data.Payload = request.data.Payload

        response = request_pb2.GenericResp()
        response.msg = "received transaction"
        response.status = 200
        # TODO: Add txn to node's txnpool
        return response