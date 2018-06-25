from trueconsensus.fastchain import node, record_pbft
from trueconsensus.proto import request_pb2#, request_pb2_grpc

n = node.Node(
    0,
    0,
    5,
    5,
    5
)

req = request_pb2.Request()

record_pbft(n.debuglog, req)
