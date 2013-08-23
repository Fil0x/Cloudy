import sys
if ".." not in sys.path:
    sys.path.append("..")

import threading
import logging
import time
from simpleflake import simpleflake
import lib.Upload as up
from lib.Authentication import AuthManager

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-15s) %(message)s',
                    )

logging.debug('Creating client...')                    
dbClient = AuthManager().dropboxAuthentication()
logging.debug('Client created!')
        
class MyThreadWithArgs(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.worker = up.DropboxUploader(self.args)
        self.worker.client = dbClient
        self.state = -1 #It can be 0 for stop when the next chunk is uploaded
                        #or 1 for delete the upload.

    def run(self):
        logging.debug('Starting Upload of the file:{}'.format(self.args))
        for i in self.worker.upload_chunked():
            logging.debug(i)
            if self.state == 0:
                return #send signal to UI
            elif self.state == 1:
                return #delete the thread, dont update the ui even if 
                       #a chunk is uploaded in the meantime.
                
        self.worker.finish('/new.pdf') #change path
        logging.debug('Upload completed.') #write to history with global lock
        #raise event to inform user
        
        return

paths = [r"C:\Users\Fadi\Desktop\03.Colloquial Swedish 2007.pdf"]

t = MyThreadWithArgs(name=str(simpleflake()), args=paths[0])
t.start()