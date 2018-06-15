# PBFT implementation in python

This is a `Practical Byzantine Fault Tolerance` implementation of Miguel Castro and Barbara Liskov's [paper from MIT CS Lab](pmg.csail.mit.edu/papers/osdi99.pdf)

### Setup

#### Configure paths and tunables

Fill up the config files `conf/pbft_logistics.cfg` and `conf/pbft_tunables.yaml` or use defaults.

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
# change to folder trueconsensus
cd trueconsensus/

# generate proto/requests_pb2.py from proto/requests.proto file
./utils/generate_proto.sh

# generate asymm keypairs
python -m utils.make_keys

# generate requests
python -m utils.generate_requests_dat
```

### Run

Server: `./engine.py`

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
