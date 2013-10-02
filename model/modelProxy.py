import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import Queue
import datetime
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
    upload_queue = Queue.Queue()
    history_queue = Queue.Queue()

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.active_threads = {} # {'id':UploadThread, ...}
        self.model = Model()
        self.logger = logger.logger_factory(self.__class__.__name__)

        self.upt = UploadSupervisorThread(self.upload_queue, self.history_queue, self)
        self.att = AddTaskThread(self.add_queue, self.upload_queue, self)
        self.ht  = HistoryThread(self.history_queue, self)
        self.upt.start()
        self.att.start()
        self.ht.start()

        #self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uq)

    #Exposed functions
    def add_file(self, service, path):
        assert(service in local.services)

        self.add_queue.put(('add', service, path))

    def stop_file(self, id):
        assert(id in self.active_threads)

        self.upload_queue.put(('stop', id))

    def delete_file(self, id):
        assert(id in self.active_threads)

        self.upload_queue.put(('delete', id))

    def resume_file(self, service, id):
        assert(service in local.services)

        r = self.model.uq.get(service, id)
        if 'error' in r:
            return #notify controller that the path is invalid
        self.add_queue.put(('resume', service, id, r))

    def get_history(self):
        r = self.model.uq.get_history()
        self.logger.debug('got item')
        return r
        
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
        self.logger.debug('Starting uploads...')
        r = self.model.uq.get_running()

        for s, v in r.iteritems():
            for id, data in v.iteritems():
                self.logger.debug('Item added: {}/{}'.format(s, id))
                self.add_queue.put(('resume', s, id, data))

    def stop_uploads(self):
        self.logger.debug('Stopping ALL uploads...')
        for k, v in self.active_threads.iteritems():
            self.logger.debug('Stopping: {}...'.format(k))
            v.state = 1

    #End of exposed functions

    def add(self, service, path):
        return self.model.uq.add(service, path)

    def save(self):
        self.model.uq.save()

    def authenticate(self, service):
        return self.model.am.authenticate(service)

    def delete(self, service, id):
        self.model.uq.delete(service, id)

class HistoryThread(threading.Thread):
    def __init__(self, in_queue, proxy, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.proxy = proxy
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

    def run(self):
        while True:
            msg = msg = self.in_queue.get()
            self.logger.debug('Got msg')
            if msg[0] in 'add':
                self.proxy.model.uq.add_history(msg[1], msg[2], **msg[3])
                self.logger.debug('added item:{}'.format(msg[2]))
                self.proxy.delete(msg[1], msg[2])
                del self.proxy.active_threads[msg[2]]
                #update ui
            elif msg[0] in 'remove':
                self.proxy.uq.delete_history(msg[1], [msg[2]])
                self.logger.debug('removed item')
                #update ui

class UploadSupervisorThread(threading.Thread):
    def __init__(self, in_queue, out_queue, proxy, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue #History queue for the upload threads
        self.proxy = proxy
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

    def run(self):
        while True:
            msg = self.in_queue.get()
            if msg[0] in 'add':
                t = UploadThread(msg[3], msg[1], self.out_queue, msg[2])
                self.proxy.active_threads[msg[2]] = t
                t.start()
                self.logger.debug('Started!')
            elif msg[0] in 'stop':
                '''Get the thread, change its state to 1, remove it
                   from the active_threads.
                '''
                self.proxy.active_threads[msg[1]].state = 1
                del self.proxy.active_threads[msg[1]]
            elif msg[0] in 'delete':
                '''Get the thread, change its state to 2, remove it
                   from the active_threads.
                '''
                t = self.proxy.active_threads[msg[1]]
                t.state = 2
                self.proxy.delete(t.service, msg[1])
                del self.proxy.active_threads[msg[1]]

class AddTaskThread(threading.Thread):

    def __init__(self, in_queue, out_queue, proxy, **kwargs):
        ''' in_queue=add_queue, out_queue=upload_queue '''
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue
        self.proxy = proxy
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

    def run(self):
        while True:
            #Block here until we have an item to add.
            msg = self.in_queue.get()
            self.logger.debug('Authenticating with {}'.format(msg[1]))
            #is it cached?
            client = self.proxy.authenticate(msg[1])
            self.logger.debug('Authentication done')
            #Errorrrrsssss
            if msg[0] in 'add':
                id, d = self.proxy.add(msg[1], msg[2])
                if 'error' in d:
                    pass #send message to controller, invalid path
                d['uploader'].client = client

                self.logger.debug('Putting the uploader in queue.')
                self.out_queue.put(('add', msg[1], id, d['uploader']))
            elif msg[0] in 'resume':
                self.logger.debug('Resuming...')
                msg[3]['uploader'].client = client
                self.out_queue.put(('add', msg[1], msg[2], msg[3]['uploader']))

class UploadThread(threading.Thread):
    def __init__(self, uploader, service, out_queue, id, **kwargs):

        threading.Thread.__init__(self, **kwargs)
        self.worker = uploader #Uploader already has a validated client.
        self.service = service
        self.id = id
        self.out_queue = out_queue
        self.logger = logger.logger_factory(self.__class__.__name__)
        self._state = 0

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        assert(value in range(3))

        self.logger.debug('Changing state to {}'.format(value))
        self._state = value

    def run(self):
        self.logger.debug('Starting:{}'.format(self.id))
        for i in self.worker.upload_chunked():
            self.logger.debug('Uploaded:{}'.format(i))
            if self._state == 1:
                self.logger.debug('Paused:{}'.format(i))
                if self.service in 'Dropbox':
                    return #break and check if progress == 100%
                else:
                    return #send signal to UI
            elif self.state == 2:
                self.logger.debug('Deleted:{}'.format(i))
                return #delete the thread, dont update the ui even if
                       #a chunk is uploaded in the meantime.

        #If I reach this point, the upload is complete and I have to save it to the history.        
        d = {}
        if self.service in 'Dropbox':
            response = self.worker.finish('{}{}'.format(self.worker.remote, os.path.basename(self.worker.path)))
            path = response['path']
            #Get the share link
            url = self.worker.client.share(path)['url']
            #Create the dictionary
            d['name'] = os.path.basename(self.worker.path)
            d['date'] = str(datetime.datetime.now())
            d['path'] = path
            d['link'] = url
            self.logger.debug('Putting in queue.')
            self.out_queue.put(('add', self.service, self.id, d))
            #send signal to UI
        elif self.service in 'GoogleDrive':
            d['name'] = os.path.basename(self.worker.path)
            d['date'] = str(datetime.datetime.now())
            d['path'] = self.worker.title
            d['link'] = self.worker.sharelink
            self.logger.debug('Putting in queue.')
            self.out_queue.put(('add', self.service, self.id, d))
            #send signal to UI
        return
