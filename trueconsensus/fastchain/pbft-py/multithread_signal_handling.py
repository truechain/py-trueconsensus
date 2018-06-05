from threading import Thread
from random import random
import signal
import time
import sys

stop_requested = False    

def sig_handler(signum, frame):
    sys.stdout.write("handling signal: %s\n" % signum)
    sys.stdout.flush()

    global stop_requested
    stop_requested = True

def simple_target(a):
    print("hello - %s - %s" %(a, random()))

def run(a):
    sys.stdout.write("run started\n")
    sys.stdout.flush()

    while not stop_requested:
        simple_target(a)
        time.sleep(1)
        
    sys.stdout.write("run exited\n")
    sys.stdout.flush()

signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT, sig_handler)

threads = []

for i in range(3):
    thread = Thread(target=run, args=[i])
    thread.start()
    threads.append(thread)
    
for thread in threads:
    thread.join()

sys.stdout.write("join completed\n")
sys.stdout.flush()
