from Crypto.Hash import SHA256
import struct
import random
import cbor

# import sig
from trueconsensus.proto import request_pb2, request_pb2_grpc
from trueconsensus.fastchain import ecdsa_sig as sig
from trueconsensus.fastchain.config import _logger

def gen_txn_data(txn_data):
    """
    """
    # txn = request_pb2.Transaction()
    # nonce = 21
    # gasprice = 18000000000
    # startgas = 100000
    # to = '0xa593094cebb06bf34df7311845c2a34996b52324'
    # value = 1000000000000
    # data = ''
    # sender = "0xc6f4f527587ea4a03aa85e0322783592367c1b9a"
    # r = "0xab90122dc4e4bbdbb14ef22ad3ae21aecc19a1c90a9c8989c68b26cc782ff303"
    # s ="0x36e5f275147049d3afd5d33b735cc9313d2c1aad3ab401aefdce678128e2f1d0"
    # v = "0x1c"
    # r = int(r, 16)
    # s = int(s, 16)
    # v = int(v, 16)    
    txn_data.AccountNonce = random.randint(1,999)
    txn_data.Price = random.randint(500, 1000)
    txn_data.GasLimit = random.randint(10000,50000)
    txn_data.Recipient = b'0xa593094cebb06bf34df7311845c2a34996b52324'
    txn_data.V = int("0x1c", 16)
    txn_data.R = int("0xab90122dc4e4bbdbb14ef22ad3ae21aecc19a1c90a9c8989c68b26cc782ff303", 16)
    txn_data.S = int("0x36e5f275147049d3afd5d33b735cc9313d2c1aad3ab401aefdce678128e2f1d0", 16)
    txn_data.Amount = random.randint(1,999) 
    fin_entities = ["CDO", "CLO", "MBS", "ABS","CDS", "Derivative", "BDO"]
    payload = {
        "txnType": random.choice(fin_entities),
        "votecount": random.randint(1,999)
    }
    txn_data.payload = cbor.dumps(payload)
    return txn_data

def add_sig(key, _id, seq, view, req_type, message, txpool=None, timestamp=None):
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
    if txpool:
        # use rlp and maybe change add_sig() to a class inheriting
        block = inner.block
        # txn = req.Transactions.add()
        block.Transactions.extend(txpool)
    if timestamp:
        inner.timestamp = timestamp
    #req.inner = inner
    b = inner.SerializeToString()
    h = SHA256.new()
    h.update(b)
    digest = h.digest()
    # import pdb; pdb.set_trace()
    s = sig.sign_proto_key(key, digest)
    # msg_sig = req.sig
    req.sig = s
    req.dig = digest
    return req

def check(key, req):
    id = req.inner.id
    #key = sig.get_signing_key(id)

    digest_recv = req.dig
    sig_recv = req.sig
    block = req.inner.block

    i = req.inner.SerializeToString()
    h = SHA256.new()
    h.update(i)
    digest = h.digest()
    # _logger.debug("check(%s) against (%s)" % (key, req))
    # import pdb; pdb.set_trace()
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


# class FastChainServicer(request_pb2_grpc.FastChainServicer):
#     # send_ack is exposed here
#     def Send(self, request, context):
#         response = request_pb2.GenericResp()
#         response.msg = request.inner.type
#         response.status = send_ack(request.inner.id)
#         # TODO: add request to node's outbuffmap and log this request
#         return response
    
#     def Check(self, request, context):
#         response = request_pb2.GenericResp()
#         response.msg = request.inner.type
#         # import pdb; pdb.set_trace()
#         response.status = send_ack(request.inner.id)
#         # TODO: add request to node's log
#         return response

#     def NewTxnRequest(self, request, context):
#         # response = request_pb2.Transaction()
#         # data = response.data
#         # data.AccountNonce = request.data.AccountNonce
#         # data.Price = request.data.Price
#         # data.GasLimit = request.data.GasLimit
#         # data.Recipient = request.data.Recipient
#         # data.Amount = request.data.Amount
#         # data.Payload = request.data.Payload

#         response = request_pb2.GenericResp()
#         response.msg = "received transaction"
#         response.status = 200
#         # TODO: Add txn to node's txnpool
#         return response
