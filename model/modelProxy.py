import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import Queue
import threading

import local
import logger
import AppFacade
import lib.Upload
from model import Model

from PyQt4 import QtCore
import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'
    
    add_queue = Queue.Queue() 
    stop_queue = Queue.Queue()
    upload_queue = Queue.Queue()
    finished_queue = Queue.Queue()

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.active_threads = {} # {'id':UploadThread, ...}
        self.model = Model()
        self.logger = logger.logger_factory(self.__class__.__name__)
        self._create_clients() #TODO
        
        self.upt = UploadSupervisorThread(self.upload_queue, self)
        self.att = AddTaskThread(self.add_queue, self.upload_queue, self)
        self.upt.start()
        self.att.start()
        
        #self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uq)

    def _create_clients(self):
        #Change this to create only the clients that the user uses.
        self.logger.debug('Init: creating clients.')
        
    def add_file(self, service, path):
        ''' The message that will be added by add() will have the following form:
            tuple: ('add', service, path)
        '''
        assert(service in local.services)
        
    
        self.add_queue.put(('add', service, path))
        
    def detailed_view_data(self):
        #TODO: change it
        data = []
        for service, items in self.model.uq.pending_uploads.iteritems():
            for key, d in items.iteritems():
                if len(d):
                    name = os.path.basename(d['uploader'].path)
                    progress = round(float(d['uploader'].offset)/d['uploader'].target_length, 2)
                    data.append([name, service, d['uploader'].remote, d['status'],
                              progress, d['conflict'], 'Not ready', key])

        return data

    def start_uploads(self):
        pass

    def add(self, service, path):
        return self.model.uq.add(service, path)

    def save(self):
        self.model.uq.save()

    def authenticate(self, service):
        return self.model.am.authenticate(service)
        
    def delete(self, service, key):
        self.model.uq.delete(service, key)
 
class UploadSupervisorThread(threading.Thread):
    def __init__(self, in_queue, proxy, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        
        self.in_queue = in_queue
        self.proxy = proxy
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')
        
    def run(self):
        while True:
            msg = self.in_queue.get()
            if msg[0] in 'add':
                t = UploadThread(msg[3], msg[1])
                self.proxy.active_threads[msg[2]] = t
                t.start()
                self.logger.debug('Started!')
 
class AddTaskThread(threading.Thread):

    def __init__(self, in_queue, out_queue, proxy, **kwargs):
        ''' in_queue=add_queue, out_queue=upload_queue '''
        threading.Thread.__init__(self, **kwargs)
        
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.proxy = proxy
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.daemon = True
        self.logger.debug('Initialized')
        
    def run(self):
        while True:
            #Block here until we have an item to add.
            msg = self.in_queue.get()
            if msg[0] in 'add':
                '''Ok, we got an 'add' message. The actions that we have to take are:
                   1)Check the client cache for an existent client.
                    1a)If there is a client, check if its working.
                    1b)If the client is invalid then create a new one.
                     (invalid tokens??)
                   2)Create an uploader.
                   3)Put him in the upload_queue.
                   4)Read next message.
                '''
                self.logger.debug('Authenticating with {}'.format(msg[1]))
                client = self.proxy.authenticate(msg[1])
                if not client:
                    self.logger.debug('fak')
                
                #Errorrrrsssss
                id, uploader = self.proxy.add(msg[1], msg[2])
                uploader.client = client
                self.logger.debug('Putting the uploader in queue.')
                self.out_queue.put(('add', msg[1], id, uploader))

class UploadThread(threading.Thread):
    def __init__(self, uploader, service, init_state=0, **kwargs):

        threading.Thread.__init__(self, **kwargs)
        self.worker = uploader #Uploader already has a validated client.
        self.service = service
        self.logger = logger.logger_factory(self.__class__.__name__)
        self._state = init_state #It can be 1 to stop when the next chunk is uploaded
                        #or 2 to delete the upload.

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        assert(value in range(3))

        self._state = value

    def run(self):
        for i in self.worker.upload_chunked():
            self.logger.debug('Uploaded:{}'.format(i))
            if self._state == 1:
                self.logger.debug('Paused:{}'.format(i))
                return #send signal to UI
            elif self.state == 2:
                return #delete the thread, dont update the ui even if
                       #a chunk is uploaded in the meantime.

        if self.service in 'Dropbox':
            self.worker.finish('{}{}'.format(self.worker.remote, os.path.basename(self.worker.path)))
        return
