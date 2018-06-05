import request_pb2
import proto_message as message
import socket
import config
import sys, struct
import threading
import select
import time
import socks
import time

kill_flag = False
start_time = 0
def recv_response(n):
    global kill_flag
    count = 0
    print "RECEIVING"
    s = socket.socket()
    p = select.epoll()
    ip, port = config.client
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(('0.0.0.0', port))
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
            count += 1
            if req.inner.seq % 100 == 0:
            #if True:
                print "SEQUENCE:", req.inner.seq
        #if req.inner.seq == n:
        if count == n * len(config.RL):
            kill_flag = True
            print 'time', end_time - start_time

if len(sys.argv) == 2:
    n = int(sys.argv[1])
else:
    n = 1000

id = 9

t = threading.Thread(target=recv_response, args=[n])
t.daemon = True
t.start()
m = open("reqs.dat", "rb").read()

print "Loaded Messages"
print "Starting send"
sock_list = []
for i in range(500):
    b = m[:4]
    size = struct.unpack("!I", b)[0]
    m = m[size+4:]
start_time = time.time()
for i in range(0,n):
    b = m[:4]
    size = struct.unpack("!I", b)[0]
    for ip, port in config.RL:
        try:
            #s = socket.socket()
            # import pdb; pdb.set_trace()
            r = socks.socksocket()
            # r.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", config.TOR_SOCKSPORT[config.N], True)
            ## r.setblocking(0)
            r.connect((ip, port))
            # s.connect((ip,port))
            r.send(m[:size+4])
            # s.send(m[:size+4])
            # sock_list.append(s)
            sock_list.append(r)
            r.close()
            # s.close()
        except Exception, e:  # broad catch
            print "failed to send to", ip, port, 'due to', e
            pass
    #s2 = socket.socket()
    #s2.connect(config.RL[0])
    #s2.send(m[:size+4])
    #s2.close()
    m = m[size+4:]

print "Done sending... wait for receives"
while True:
    time.sleep(1)
    if kill_flag:
        # give laggy requests some time to show up
        time.sleep(1)
        sys.exit()

