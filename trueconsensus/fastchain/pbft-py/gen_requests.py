import request_pb2
import proto_message as message
import socket, random
#import config
import sys, struct
import sig, ecdsa_sig

if len(sys.argv) >= 2:
    n = int(sys.argv[1])
else:
    n = 1000

if len(sys.argv) >= 3:
    batch_size = int(sys.argv[2])
else:
    batch_size = 1024

print "Generating",n,"requests with batch size",batch_size
#id = 9
offset = 0
#offset = random.randint(0,99999999)
print "Offset:", offset

f = open("reqs.dat","wb")

key_dict = {}
for i in range(n):
    key_dict[i] = sig.get_signing_key(i)

# import pdb; pdb.set_trace()
ecdsa_pub = ecdsa_sig.get_verifying_key(0)
tmp = open("hello_0.dat", 'r')
ecdsa_sig = tmp.read()
tmp.close()

for i in range(0,n):
    print "for N: ",i
    #r = 11
    #r2 = 12
    r = random.randint(1,n)
    r2 = random.randint(n/2,n)
    #amount = random.randint(0,100)
    amount = 50
    msg = "TRAN" + str(amount).zfill(4) + str(r2).zfill(4) + ecdsa_pub.to_string()
    if i == 0:
        print len(ecdsa_pub.to_string()), "ECDSA"
    req = message.add_sig(key_dict[r],r,0,0,"REQU",msg,i)
    req.sig = ecdsa_sig
    msg = req.SerializeToString()
    if i == 0:
        print "one request:", len(msg)
    ################################
    #padding = "0123456789" * 10
    #msg += padding * 1024
    #msg += "x" * (400 - len(msg))
    msg += msg * (batch_size-1)
    ################################
    key = key_dict[r]
    temp = message.add_sig(key,r,0,0,"REQU",msg,i+offset)
    size = temp.ByteSize()
    if i == 0:
        print "inner message:", len(msg)
        print size
    b = struct.pack("!I", size)
    f.write(b+temp.SerializeToString())

print "Finished Message Generation"



