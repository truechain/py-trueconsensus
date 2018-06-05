import os
# This Replica ID
ID = 0

# Number of replicas
N = 4

# Number of failures we can tolerate
MAX_FAIL = 1

# REPLICA LIST
# IP, port
RL = []
RL.append(("127.0.0.1", 8001))
RL.append(("127.0.0.1", 8002))
RL.append(("127.0.0.1", 8003))
RL.append(("127.0.0.1", 8004))

client = (("127.0.0.1", 9001))

# KEY DIRECTORY
KD = os.getcwd() + "/keys"
print KD
