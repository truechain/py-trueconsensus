import request_pb2
import proto_message as message
import socket
import config
import sys, struct, time
import threading
from threading import Thread

class reqs(Thread):
    def __init__(self, sock, msg_list, ret, index):
        Thread.__init__(self)
        self.sock = sock
        self.msg_list = msg_list
        self.ret = ret
        self.index = index

    def run(self):
        for msg in self.msg_list:
            self.sock.send(msg)
        self.start_time = time.time()

        data = self.sock.recv(4096)
        self.sock.close()
        try:
            req = request_pb2.Request()
            size = struct.unpack("!I",data[:4])[0]
            req.ParseFromString(data[4:size+4])
            if req.inner.msg != "APPROVED" and req.inner.msg != "INVALID":
                self.ret[self.index] = None
                return None
        except:
            self.ret[self.index] = None
            return None
        self.ret[self.index] = (time.time() - self.start_time, req.inner.msg)
        return time.time() - self.start_time

if len(sys.argv) == 2:
    n = int(sys.argv[1])
else:
    n = 1000

id = 9

m = open("reqs.dat","rb").read()

print "Loaded Messages"
print "Starting send"
start_time = time.time()
reqs_list = []
ret_list = [None]*n
for i in range(0,n):
    b = m[:4]
    size = struct.unpack("!I",b)[0]
    s = socket.socket()
    ip,port = config.RL[0]
    s.connect((ip,port))
    #s.send(m[:size+4])
    req_obj = reqs(s,[m[:size+4]], ret_list, i)
    reqs_list.append(req_obj)
    req_obj.start()
    #s.close()
    m = m[size+4:]
    while threading.active_count() > 5000:
        print "more than 5k threads, sleeping 1 second"
        time.sleep(1)

print "Done sending"
total = 0.0
lat_total = 0.0
app = 0
inv = 0
failed = 0
for r in reqs_list:
    r.join()

stop_time = time.time()
for i in ret_list:
    if i is not None:
        lat,msg = i
        total += 1
        lat_total += lat
        if msg == "APPROVED":
            app += 1
        if msg == "INVALID":
            inv += 1
    else:
        failed += 1

print "TOTAL:", total
if total > 0:
    print "AVG LATENCY:", lat_total/total
print "FAILED:" , failed
print "APPROVED:", app
print "INVALID:", inv
print "\nTime elapsed: ", stop_time - start_time
print n / (stop_time - start_time) , "tx/sec"
