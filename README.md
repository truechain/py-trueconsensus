# Prototype Hybrid Consensus
prototype for hybrid consensus (Pass and Shi). https://eprint.iacr.org/2016/917.pdf


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
