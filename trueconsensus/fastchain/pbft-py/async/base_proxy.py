import config
import socket
import select, time
import sys, struct
import request_pb2

offset = 100
recv_mask = select.EPOLLIN | select.EPOLLPRI | select.EPOLLRDNORM
send_mask = select.EPOLLOUT | select.EPOLLWRNORM
fdmap = {}
buffmap = {}
outbuffmap = {}

def serialize(req):
    size = req.ByteSize()
    b = struct.pack("!I", size)
    return b + req.SerializeToString()

def parse_request(request_bytes, fd):
    req = request_pb2.Request()
    req.ParseFromString(request_bytes)
    id = req.inner.id
    print "parsing a req from ", id, req.inner.type
        
    retry = True
    ip,port = portmap[fd]
    print "attempting connection on", ip, port+offset
    count = 0
    while retry:
        count += 1
        try:
            time.sleep(0.01)
            s = socket.socket()
            s.connect((ip, port+offset))
            s.send(serialize(req))
            if req.inner.type == "INIT":
                p.register(s, recv_mask)
                fdmap[s.fileno()] = s
                buffmap[s.fileno()] = ""
                portmap[s.fileno()] = config.RL[req.inner.id]
        except:
            time.sleep(0.01)
            if count > 1000:
                raise
            continue
        retry = False
    print "done sending"
    print c.getsockname()

def clean(fd):
    p.unregister(fd)
    fdmap[fd].close()
    del fdmap[fd]
    del buffmap[fd]

l_fd = []
p = select.epoll()
portmap = {}
for ip,port in config.RL:
    # listen on original ports
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip,port))
    s.listen(50)
    s.setblocking(0)
    fdmap[s.fileno()] = s

    p.register(s)
    l_fd.append(s.fileno())

print "starting loop"
while True:
    events = p.poll()
    for fd, event in events:
        if fd in l_fd:
            #print "GOT CON"
            c,addr = fdmap[fd].accept()
            p.register(c, recv_mask)
            fdmap[c.fileno()] = c
            buffmap[c.fileno()] = ""
            outbuffmap[c.fileno()] = ""
            portmap[c.fileno()] = fdmap[fd].getsockname()
        else:
            # read event
            if event & recv_mask != 0:
                try: 
                    data = fdmap[fd].recv(10000)
                except:
                    raise
                if len(data) == 0:
                    #clean(fd)
                    pass
                buffmap[fd] += data
                #print len(buffmap[fd])
                while(len(buffmap[fd]) > 3):
                    print "parsing...", len(buffmap[fd])
                    size = struct.unpack("!I", buffmap[fd][:4])[0]
                    if len(buffmap[fd]) >= size+4:
                        parse_request(buffmap[fd][4:size+4], fd)
                        buffmap[fd] = buffmap[fd][size+4:]
                    else:
                        break
                







