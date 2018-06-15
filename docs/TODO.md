## Generic Infra

- [ ] Separate Dapp architecture: `dapps/bank.py` is currently tightly coupled with node.py. 
- [ ] no gRPC communiction between nodes yet
- [ ] add network_latency check 

## Fastchain

- [ ] nodes call quits on any error
- [ ] xyz.pem not found error on running client.py. Batch size not playing well in proto_message.message check
- [ ] complete subprotocol.py
- [ ] complete bft_committee.py
- [ ] return blocks of transactions

## Snailchain / Committee election

- [ ] complete minerva/vrf.py function
- [ ] complete snailchain/fpow.py dummy
- [ ] integrate level db wrappers
- [ ] integrate py-evm functionalities
