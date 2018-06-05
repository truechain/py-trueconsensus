import request_pb2
import proto_message as message
import socket
import config
import sys, struct
import threading
import select
import time

kill_flag = False

def recv_response(n):
    global kill_flag
    print "RECEIVING"
    s = socket.socket()
    p = select.epoll()
    ip,port = config.client
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind((ip,port))
    s.listen(50)
    p.register(s)
    f = open("client_log.txt", 'w')
    f.write(str(time.time()) + " SEQUENCE: " + "0"  + " REPLICA: " + "START" + "\n")
    while(True):
        events = p.poll()
        for fd, event in events:
            c,addr = s.accept()
            r = c.recv(4096)
            size = struct.unpack("!I", r[:4])[0]
            req = request_pb2.Request()
            req.ParseFromString(r[4:])
            #print req.inner.msg, req.inner.seq, "FROM", req.inner.id
            f.write(str(time.time()) + " SEQUENCE: " + str(req.inner.seq) + " REPLICA: " + str(req.inner.id) + "\n")
            #if req.inner.seq % 100 == 1:
            if True:
                print "SEQUENCE:", req.inner.seq, "FROM", req.inner.id, "IN VIEW", req.inner.view
        if req.inner.seq == n:
            kill_flag = True

if len(sys.argv) == 2:
    n = int(sys.argv[1])
else:
    n = 1000

id = 9

t = threading.Thread(target=recv_response, args=[n])
t.daemon = True
t.start()
m = open("reqs.dat","rb").read()

print "Loaded Messages"
print "Starting send"
sock_list = []
for ip,port in config.RL:
    s = socket.socket()
    s.connect((ip,port))
    sock_list.append(s)

for i in range(0,n):
    b = m[:4]
    size = struct.unpack("!I",b)[0]
    #for ip,port in config.RL:
    for s in sock_list:
        try:
            s.send(m[:size+4])
        except:
            raise
    m = m[size+4:]

print "Done sending... wait for receives"
for s in sock_list:
    s.close()
while True:
    time.sleep(1)
    if kill_flag:
        # give laggy requests some time to show up
        time.sleep(5)
        sys.exit()

