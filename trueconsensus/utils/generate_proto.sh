#!/bin/sh

set -e

PROTO_ROOT=proto/

if [[ -d $PROTO_ROOT ]]; then
    if [[ -f ${PROTO_ROOT%/}/request.proto ]]; then
	protoc --python_out=$PWD proto/request.proto
    else
	echo "File [${PROTO_ROOT%/}/request.proto] not found!"

	echo "Generated ${PROTO_ROOT%/}/request_pb2.py from request.proto"
    fi
else
    echo "Directory $PWD/proto not found!"
fi
