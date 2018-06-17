# Prototype Hybrid Consensus
prototype for TrueChain hybrid consensus
Refer to:
https://arxiv.org/abs/1805.01457
https://eprint.iacr.org/2016/917.pdf

## Run

Refer to `trueconsensus/README.md` for further instructions

### Parameterized by following..

Variable | Meaning |
--- | ---:|
tx | a transaction
l | sequence number of a transaction within each BFT instance
LOG | the totally ordered log each node outputs, LOG is always populated in order
log | log of one BFT instance, referred to as daily log
`log[l : l′]` | transactions numbered l to l′ in log
`log[: l]` | `log[1 : l]``
`λ` | security parameter
`α` | adversary’s fraction of hashpower
`δ` | network’s maximum actual delay
`∆` | a-priori upper bound of the network’s delay (typically loose)
csize | committee size, our protocol sets csize := λ
th | `th := ⌈csize/3⌉`, a threshold
lower(R), upper(R) | ```lower(R) := (R − 1)csize + 1, upper(R) := R · csize```
chain | a node’s local chain in the underlying snailchain protocol
`chain[: −λ]` | all but the last λ blocks of a node’s local chain
`MinersOf(chain[s : t])` | the public keys that mined each block in chain[s : t]. It is possible that several public keys belong to the same node.
`{msg}pk−1` | a signed message msg, whose verification key is pk
Tbft | liveness parameter of the underlying BFT scheme

# PBFT implementation in python

This is a `Practical Byzantine Fault Tolerance` implementation of Miguel Castro and Barbara Liskov's [paper from MIT CS Lab](pmg.csail.mit.edu/papers/osdi99.pdf)

### Setup

#### Configure paths and tunables

Fill up the config files `conf/logistics.cfg` and `conf/tunables.yaml` or use defaults.

#### Install dependencies

__Recommended__: Use a python3 virtual environment

```
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

##### Install Google's Protobuf

Download and install [google protobuf](https://github.com/google/protobuf/tree/master/python/google)

```
# brew install protobuf
OR 
# pip install protobuf
```

#### Generate required content as a precusory

Then proceed as follows:

```
# generate proto/requests_pb2.py from proto/requests.proto file
./trueconsensus/utils/generate_proto.sh

# generate asymm keypairs
python -m trueconsensus.utils.make_keys

# generate requests
python -m trueconsensus.utils.generate_requests_dat

# test your installation with 
python -m trueconsensus
```

### Run

Server: `./minerva.py`

Client: `python -m trueconsensus.client`

### Monitor logs

Client logs in terminal:

```
tail -f /var/log/truechain.client.log 
```

Server logs in another terminal:

```
tail -f /var/log/truechain/engine.log 
```

To check all the phases encountered in the log:

```
grep -Po 'Phase: \[\K[^\]]*' /var/log/truechain/engine.log  | sort | uniq

Or

sed -n -e 's/^.*Phase: \(.*]\), .*/\1/p' /var/log/truechain/engine.log | sort | uniq
```
