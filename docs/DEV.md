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


# References

### Ethereum / blockchain funda

- whitepaper https://github.com/ethereum/wiki/wiki/White-Paper#fees
- overview https://bitcoin.org/en/developer-guide#block-chain
- block architecture https://github.com/truechain/truechain-consensus-core/blob/master/pbft/src/pbft-core/node.go#L357:6
  - roots and tries https://ethereum.stackexchange.com/questions/21754/ethereum-block-structure-roots-and-tries-concept
- Build your own blockchain prototyping in py http://ecomunsing.com/build-your-own-blockchain
- Product manager's guide to blockchain https://hackernoon.com/product-managers-guide-to-blockchain-part-3-fb0cffbff7f8
- roadmap https://hackernoon.com/the-beginners-guide-to-ethereum-s-2020-roadmap-2ac5d2dd4881

### EVM

- pow func in py-evm https://github.com/ethereum/py-evm/blob/master/evm/consensus/pow.py#L76
- GAS meter costs per step, sheet for EVM https://docs.google.com/spreadsheets/d/1m89CVujrQe5LAFJ8-YAUCcNK950dUzMQPMJBxRtGCqs/edit#gid=0
- difficulty in POW https://en.bitcoin.it/wiki/Difficulty

### Contracts

- solidity compilation in python http://ecomunsing.com/tutorial-controlling-ethereum-with-python
- explaining social applications of smart contracts https://blockgeeks.com/guides/smart-contracts/
- 

### Networking

- list of network IDs https://ethereum.stackexchange.com/questions/17051/how-to-select-a-network-id-or-is-there-a-list-of-network-ids
- bootnodes https://github.com/ethereum/go-ethereum/blob/master/params/bootnodes.go
- DB <-> networking seeding out with bootnodes https://github.com/ethereum/go-ethereum/blob/master/p2p/discover/database.go#L38:31
- Kadelmia peer selection https://github.com/ethereum/wiki/wiki/Kademlia-Peer-Selection#peer-addresses
- Kadelmia File Storage KFS by Storj https://github.com/storj/kfs
- 

### Blocks / Transactions

- validate txn func https://github.com/ethereum/pyethereum/blob/master/ethereum/processblock.py#L78

- example verification in py with ecdsa recovery https://ethereum.stackexchange.com/questions/19328/python-ecdsa-public-key-recovery

- lifecycle of ethereum txn https://medium.com/blockchannel/life-cycle-of-an-ethereum-transaction-e5c66bae0f6e
  - Not all nodes will accept your transaction. Some of these nodes might have a setting to accept only transactions with certain minimum gas price. If you have set a gas price lower than that limit, that node will just ignore your transaction.

- block.py in ethereum https://github.com/ethereum/pyethereum/blob/develop/ethereum/block.py
- transactions.py in ethereum https://github.com/ethereum/pyethereum/blob/develop/ethereum/transactions.py

- struct https://github.com/ethereum/go-ethereum/blob/1990c9e6216fd6b25fdf6447844f36405b75c18e/core/types/transaction.go
- blockchain struct https://github.com/ethereum/go-ethereum/blob/master/core/blockchain.go


### Definitions

- uncles https://www.reddit.com/r/ethereum/comments/3c9jbf/wtf_are_uncles_and_why_do_they_matter/
  - related: GHOST incentive model for uncles https://eprint.iacr.org/2013/881.pdf

- Coinbase https://bitcoin.stackexchange.com/questions/4571/what-is-the-coinbase

### Database

- level db py wrapper https://plyvel.readthedocs.io/en/latest/user.html#basic-operations
- database testing in ethereum https://github.com/ethereum/go-ethereum/blob/master/p2p/discover/database_test.go


### Cryptography

#### Python / ECDSA

- Sign / verify message with ecdsa https://stackoverflow.com/questions/34451214/how-to-sign-and-verify-signature-with-ecdsa-in-python
- ECDSA tests https://github.com/warner/python-ecdsa/blob/master/src/ecdsa/test_pyecdsa.py
- PEM/DER formatting https://bitcoin.stackexchange.com/questions/41666/pem-format-for-ecdsa
- sawtooth payload encoding w/ cbor https://sawtooth.hyperledger.org/docs/core/releases/1.0.0rc4/_autogen/sdk_submit_tutorial_python.html
- VRS fields in txn
  - what's VRS? https://bitcoin.stackexchange.com/questions/38351/ecdsa-v-r-s-what-is-v
  - transaciton class with rlp https://github.com/ethereum/pyethereum/blob/develop/ethereum/transactions.py#L40
  - public key recovery https://ethereum.stackexchange.com/questions/19328/python-ecdsa-public-key-recovery
- v,r,s formation from ecdsa signing in ethereum ecsign() https://github.com/ethereum/pyethereum/blob/3c129aeaa374b223723e522fc2abb8baf6f3f142/ethereum/utils.py#L112:45
- Team Keccak https://keccak.team/sponge_duplex.html
- A tale of 2 curves https://blog.enuma.io/update/2016/11/01/a-tale-of-two-curves-hardware-signing-for-ethereum.html


### VRF

- IETF proposal draft https://tools.ietf.org/id/draft-goldbe-vrf-01.html

### Protocol buffers / serialization

#### gRPC / protobuf

- comprehensive example https://goel.io/grpc-100/
- py grpc https://grpc.io/docs/tutorials/basic/python.html
- protobuf data types https://developers.google.com/protocol-buffers/docs/proto
- using grpc in py blog https://blog.codeship.com/using-grpc-in-python/
- adding to repeated fields https://developers.google.com/protocol-buffers/docs/reference/python-generated#repeated-fields
- generated gRPC code ref https://grpc.io/docs/reference/python/generated-code.html
- framework interfaces doc https://grpc.io/grpc/python/grpc.framework.interfaces.face.html
- framework subpackages https://grpc.io/grpc/python/grpc.html#subpackages

#### RLP 

- RLP v/s Protobuf https://github.com/prysmaticlabs/geth-sharding/issues/150
- Ethereum design rationale for RLP https://github.com/ethereum/wiki/wiki/Design-Rationale#rlp
- Definition https://github.com/ethereum/wiki/wiki/RLP

### Private blockchain materials

- Genesis block https://hackernoon.com/heres-how-i-built-a-private-blockchain-network-and-you-can-too-62ca7db556c0

### Istanbul BFT

- BFT state machine EIP https://github.com/ethereum/EIPs/issues/650

- Slides https://www.slideshare.net/YuTeLin1/istanbul-bft

- EIP code flow https://sourcegraph.com/github.com/getamis/go-ethereum@c754738/-/blob/consensus/istanbul/core/

- tools/utils for benchmarking, genesis, graphing, orchestration https://github.com/getamis/istanbul-tools and https://medium.com/getamis/istanbul-bft-ibft-c2758b7fe6ff

### Generic / programming

- typing feature py 3.5+ https://docs.python.org/3/library/typing.html
  - https://stackoverflow.com/questions/2489669/function-parameter-types-in-python


