import sys
if ".." not in sys.path:
    sys.path.append("..")

import threading
import logging
import time
import random

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-15s) %(message)s',
                    )

class Worker(object):
    
    def __init__(self, id):
        self.stopped = False
        self.id = id
        self.ran = random.randint(0,4)
    
    def heavyStuff(self):
        for i in range(5):
            if not self.stopped and i != self.ran:
                time.sleep(2)
            else:
                return i
        return 0
        
class MyThreadWithArgs(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.worker = Worker(args)
        
        return

    def run(self):
        logging.debug('Calling heavyStuff')
        i = self.worker.heavyStuff()
        logging.debug('Worker finished with value: {}'.format(i))
        
        return

for i in range(5):
    t = MyThreadWithArgs(args=i)
    t.start()