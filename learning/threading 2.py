import sys
if ".." not in sys.path:
    sys.path.append("..")

import threading
import logging
import time
import random
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
        
        return

    def run(self):
        logging.debug('Starting Upload of the file:{}'.format(self.args))
        for i in self.worker.upload_chunked():
            logging.debug(i)
        logging.debug('Upload completed.')
        self.worker.finish('/new.pdf')
        
        return

paths = [r"C:\Users\Fadi\Desktop\03.Colloquial Swedish 2007.pdf"]

for i in paths:
    t = MyThreadWithArgs(args=i)
    t.start()