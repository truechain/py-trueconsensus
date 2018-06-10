import sys
import config

if len(sys.argv) == 2:
    batch_size = int(sys.argv[1])
else:
    batch_size = 1024

filename = "client_log.txt"

f = open(filename, 'r')
lines = f.readlines()
f.close()
num_replicas = len(config.RL)
first = float(lines[0].strip().split(' ')[0])
last = float(lines[-1].strip().split(' ')[0])
diff = last - first
total = len(lines)-1
print("Total time elapsed:", diff)
print("Total responses:", total)
print("Total replicas:", num_replicas)
print("Batch size:", batch_size)
print("Batches per second:", (total/float(num_replicas))/diff)
print("Requests per second:", ((total/float(num_replicas))/diff)*batch_size)
print("Latency:", 1/((total/float(num_replicas))/diff))


for line in lines:
    sp = line.strip().split(' ')
