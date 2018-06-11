# PBFT implementation in python

This is a `Practical Byzantine Fault Tolerance` implementation of Miguel Castro and Barbara Liskov's [paper from MIT CS Lab](pmg.csail.mit.edu/papers/osdi99.pdf)

### Setup

#### Install Google's Protobuf

Download and install [google protobuf](https://github.com/google/protobuf/tree/master/python/google)

```
# brew install protobuf
OR 
# pip install protobuf
```

#### Configure paths and tunables

Fill up the config files `pbft_logistics.cfg` and `pbft_tunables.yaml` or use defaults.


#### Install dependencies

__Recommended__: Use a python3 virtual environment

```
virtualenv -p python3 venv
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Generate required content as a precusory

Then proceed as follows:

```
# generate requests_pb2.py from requests.proto file
./proto.sh

# generate asymm keypairs
python make_keys.py

# generate requests
./generate_requests_dat.py 
```

### Run

Server: `./server.py`

Client: `./client.py`

### Monitor logs

Client logs in terminal:

```
tail -f /var/tmp/log/pbft_client.log 
```

Server logs in another terminal:

```
tail -f /var/tmp/log/pbft_complete_run.log 
```
