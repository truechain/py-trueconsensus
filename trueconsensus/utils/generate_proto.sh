#!/bin/sh

set -e

PROTO_ROOT=trueconsensus/proto/
PROTO_FILEPATH=${PROTO_ROOT%/}/request.proto

if [[ -d $PROTO_ROOT ]]; then
    if [[ -f ${PROTO_ROOT%/}/request.proto ]]; then
        # protoc --python_out=$PWD $PROTO_FILEPATH
        python -m grpc_tools.protoc -I $PROTO_ROOT --python_out=$PROTO_ROOT --grpc_python_out=$PROTO_ROOT $PROTO_FILEPATH
    else
        echo "File [$PROTO_FILEPATH] not found!"
        echo "Generated ${PROTO_ROOT%/}/request_pb2.py from request.proto"
    fi
else
    echo "Directory $PROTO_ROOT not found!"
fi

sed -i s#'import request_pb2.*'#'from . import request_pb2 as request__pb2'#g trueconsensus/proto/request_pb2_grpc.py
