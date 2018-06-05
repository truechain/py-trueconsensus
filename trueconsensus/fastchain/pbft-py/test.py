from threading import Timer, Thread
import time, signal, sys


class test(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.options = {"beat" : self.beat}

    def sigint_handler(self, signum, flag):
        print "handler"
        self.t.cancel()
        sys.exit()
        
    def beat(self):
        print "beat"

    def run(self):
        print "start"    
        #signal.signal(signal.SIGINT, self.sigint_handler)

        self.t = Timer(5, self.options["beat"])
        self.t.start()

        
        i = 5
        while i < 5:
            print i
            i = i + 1
            time.sleep(1)

        return "RETURN"
            
class mthread(Thread):
    def __init__(self, output):
        Thread.__init__(self)
        self.output = output

    def run(self):
        print self.output.msg
        return

class tester:
    def __init__(self, msg):
        self.msg = msg
    def run(self):
        self.mt = mthread((self))
        self.mt.start()

if __name__ == "__main__":
    #t = test()
    #t.start()
    #rc = t.join()
    
    t = tester("whatever...")
    t.run()
    
