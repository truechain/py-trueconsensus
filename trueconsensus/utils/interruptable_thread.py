import threading
import signal
import time
import sys


class InvalidOperationException(Exception):
    pass    


# noinspection PyClassHasNoInit
class GlobalInterruptableThreadHandler:
    threads = []
    initialized = False

    @staticmethod
    def initialize():
        signal.signal(signal.SIGTERM, GlobalInterruptableThreadHandler.sig_handler)
        signal.signal(signal.SIGINT, GlobalInterruptableThreadHandler.sig_handler)
        GlobalInterruptableThreadHandler.initialized = True

    @staticmethod
    def add_thread(thread):
        if threading.current_thread().name != 'MainThread':
            raise InvalidOperationException("InterruptableThread objects may only be started from the Main thread.")

        if not GlobalInterruptableThreadHandler.initialized:
            GlobalInterruptableThreadHandler.initialize()

        GlobalInterruptableThreadHandler.threads.append(thread)

    @staticmethod
    def sig_handler(signum, frame):
        sys.stdout.write("handling signal: %s\n" % signum)
        # sys.stdout.write("Kill signal (%s) detected. Stopping BFT node.." % signum)
        sys.stdout.flush()

        # countdown = 1
        # print("Committing deliberate suicide in %s seconds" % countdown)
        # time.sleep(countdown)
        # import pdb; pdb.set_trace()
        for thread in GlobalInterruptableThreadHandler.threads:
            # print("Active Thread Count: ", threading.active_count())
            thread.stop()

        GlobalInterruptableThreadHandler.threads = []    


class InterruptableThread:
    def __init__(self, target=None):
        self.stop_requested = threading.Event()
        self.t = threading.Thread(target=target, args=[self]) if target else threading.Thread(target=self.run)

    def run(self):
        pass

    def start(self):
        GlobalInterruptableThreadHandler.add_thread(self)
        self.t.start()

    def stop(self):
        self.stop_requested.set()

    def is_stop_requested(self):
        return self.stop_requested.is_set()

    def join(self):
        try:
            while self.t.is_alive():
                self.t.join(timeout=1)
        except (KeyboardInterrupt, SystemExit):
            self.stop_requested.set()
            self.t.join()

        sys.stdout.write("join completed\n")
        sys.stdout.flush()
