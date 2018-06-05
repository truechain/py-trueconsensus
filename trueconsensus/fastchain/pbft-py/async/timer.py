import time

class Timer:
    def __init__(self, name):
        self.name = name
        self.start = time.time()
        self.events = []

    def record(self, event):
        self.events.append((event, time.time()))

    def dump(self):
        print "Timer ", self.name
        for i in self.events:
            print "\t", i[0], i[1], i[1] - self.start
            
            
            
class request_timer:
    def __init__(self, seconds):
        self.start = time.time()
        self.duration = seconds
