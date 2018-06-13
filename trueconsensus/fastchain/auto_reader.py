import request_pb2
import proto_message as message
import socket
import config
import sys, struct

if len(sys.argv) == 2:
    n = int(sys.argv[1])
else:
    n = 1000

id = 9

m = open("reqs.dat","rb").read()

print "Loaded Messages"
print "Starting send"
sock_list = []
for i in range(0,n):
    b = m[:4]
    size = struct.unpack("!I",b)[0]
    s = socket.socket()
    ip,port = config.RL[0]
    s.connect((ip,port))
    s.send(m[:size+4])
    sock_list.append(s)
    #s.close()
    m = m[size+4:]

print "DONE"
for s in sock_list:
    try:
        req = request_pb2.Request()
        data = s.recv(4096)
        size = struct.unpack("!I",data[:4])[0]
        req.ParseFromString(data[4:])
        print req.inner.msg
    except:
        print "nothing"

