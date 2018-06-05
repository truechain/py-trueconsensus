import request_pb2
import proto_message as message
import socket, random
#import config
import sys, struct
import sig

if len(sys.argv) == 2:
    n = int(sys.argv[1])
else:
    n = 1000

#id = 9
offset = 0

f = open("reqs.dat","wb")

key_dict = {}
for i in range(10):
    key_dict[i] = sig.get_signing_key(i)

for i in range(0,n):
    r = random.randint(4,9)
    r2 = random.randint(4,9)
    amount = random.randint(0,100)
    msg = "TRAN" + str(amount).zfill(4) + str(r2).zfill(4)
    ################################
    #padding = "0123456789" * 10
    #msg += padding * 1024
    msg += msg * 1024
    ################################
    key = key_dict[r]
    temp = message.add_sig(key,r,i+1,0,"REQU",msg,i+offset)
    size = temp.ByteSize()
    b = struct.pack("!I", size)
    f.write(b+temp.SerializeToString())

print "Finished Message Generation"



