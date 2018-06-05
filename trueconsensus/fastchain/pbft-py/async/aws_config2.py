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
RL.append(("172.31.58.60", 8001))
RL.append(("172.31.58.57", 8002))
RL.append(("172.31.58.58", 8003))
RL.append(("172.31.58.59", 8004))

# KEY DIRECTORY
KD = os.getcwd() + "/keys"
print KD
