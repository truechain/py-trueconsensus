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
RL.append(("172.31.55.24", 8001))
RL.append(("172.31.48.17", 8002))
RL.append(("172.31.48.18", 8003))
RL.append(("172.31.48.16", 8004))

# KEY DIRECTORY
KD = os.getcwd() + "/keys"
print KD
