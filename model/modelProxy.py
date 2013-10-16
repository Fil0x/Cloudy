import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import Queue
import datetime
import threading

import local
import logger
import globals
import AppFacade
import lib.Upload
from model import Model

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
        self.g = globals.get_globals()

        self.upt = UploadSupervisorThread(self.upload_queue, self.history_queue, self, self.g)
        self.att = AddTaskThread(self.add_queue, self.upload_queue, self, self.g)
        self.ht  = HistoryThread(self.history_queue, self, self.g)
        self.upt.start()
        self.att.start()
        self.ht.start()

    #Exposed functions
    def add_file(self, service, path):
        assert(service in local.services)

        self.add_queue.put(('add', service, path))

    def stop_file(self, data):
        for i in data:
            assert i in self.active_threads, 'ID:{} not found'.format(i)
            self.upload_queue.put(('stop', i))

    def delete_file(self, data):
        for i in data:
            self.upload_queue.put(('delete', i[1], i[0]))

    def resume_file(self, data):
        for i in data:
            #Skip files with status Running
            r = self.model.uq.get(i[1], i[0])
            if 'error' in r:
                return #notify controller that the path is invalid
            self.add_queue.put(('resume', i[1], i[0], r))

    def get_history(self):
        r = self.model.uq.get_history()
        self.logger.debug('got item')
        return r

    def delete_history(self, data):
        for i in data:
            self.history_queue.put(('remove', i[1], i[0]))
        
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
        
    def get_status(self, service, id):
        return self.model.uq.get_status(service, id)

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
        
    def set_state(self, service, id, state):
        self.model.uq.set_state(service, id, state)

class HistoryThread(threading.Thread):
    def __init__(self, in_queue, proxy, globals, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.proxy = proxy
        self.globals = globals
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
                #There is no other easy way to send the message to the main thread
                self.proxy.facade.sendNotification(AppFacade.AppFacade.HISTORY_UPDATE_COMPACT,
                                            [self.globals, msg[1], msg[3]])
                self.proxy.facade.sendNotification(AppFacade.AppFacade.HISTORY_UPDATE_DETAILED,
                                            [self.globals, msg[1], msg[2], msg[3]])
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_DONE,
                                            [self.globals, msg[2]])
            elif msg[0] in 'remove':
                self.proxy.model.uq.delete_history(msg[1], [msg[2]])
                self.logger.debug('removed item')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.DELETE_HISTORY_DETAILED,
                                                   [self.globals, msg[2]])
                self.proxy.facade.sendNotification(AppFacade.AppFacade.DELETE_HISTORY_COMPACT,
                                                   [self.globals])
                

class UploadSupervisorThread(threading.Thread):
    def __init__(self, in_queue, out_queue, proxy, globals, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue #History queue for the upload threads
        self.proxy = proxy
        self.globals = globals
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')
        
    def run(self):
        while True:
            msg = self.in_queue.get()
            if msg[0] in 'add':
                t = UploadThread(msg[3], msg[1], self.out_queue, msg[2], 
                                 self.proxy, self.globals)
                self.proxy.active_threads[msg[2]] = t
                t.start()
                # [filename, progress, service, status, dest, conflict]
                filename = os.path.basename(msg[3].path)
                l = [self.globals, filename, '0%', msg[1], 'Running', msg[3].remote, 'TODO', msg[2]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_ADDED, l)
                self.logger.debug('Started!')
            elif msg[0] in 'resume':
                t = UploadThread(msg[3], msg[1], self.out_queue, msg[2], 
                                 self.proxy, self.globals)
                self.proxy.active_threads[msg[2]] = t
                t.start()
                # The row already exists, just update the status.
                self.proxy.set_state(msg[1], msg[2], 'Running')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_RESUMED,
                                                   [self.globals, msg[2]])
                self.logger.debug('Resumed {}!'.format(msg[2]))
            elif msg[0] in 'stop':
                self.proxy.active_threads[msg[1]].state = 1
                #Emit Pausing...
                del self.proxy.active_threads[msg[1]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_PAUSING,
                                                   [self.globals, msg[1]])
            elif msg[0] in 'delete':
                #Running->Removing
                if msg[2] in self.proxy.active_threads:
                    t = self.proxy.active_threads[msg[2]]
                    t.state = 2
                    del self.proxy.active_threads[msg[2]]
                    self.proxy.delete(msg[1], msg[2])
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVING,
                                                       [self.globals, msg[2]])
                #Paused->Removing
                else:
                    self.proxy.delete(msg[1], msg[2])
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVED,
                                                       [self.globals, msg[2]])

class AddTaskThread(threading.Thread):

    def __init__(self, in_queue, out_queue, proxy, globals, **kwargs):
        ''' in_queue=add_queue, out_queue=upload_queue '''
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue
        self.proxy = proxy
        self.globals = globals
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
                self.out_queue.put(('resume', msg[1], msg[2], msg[3]['uploader']))

class UploadThread(threading.Thread):
    def __init__(self, uploader, service, out_queue, id, proxy, globals, **kwargs):

        threading.Thread.__init__(self, **kwargs)
        self.worker = uploader #Uploader already has a validated client.
        self.service = service
        self.proxy = proxy
        self.globals = globals
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
            progress = str(round(i[0], 3)*100) + '%'
            self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_UPDATED, 
                                               [self.globals, self.id, progress])
                                               
            if self._state == 1:
                self.logger.debug('Paused:{}'.format(i))
                self.proxy.set_state(self.service, self.id, 'Paused')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_PAUSED,
                                                   [self.globals, self.id])
                if self.service in 'Dropbox':
                    return #break and check if progress == 100%
                else:
                    return #send signal to UI
            elif self.state == 2:
                self.logger.debug('Deleted:{}'.format(i))
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVED,
                                                   [self.globals, self.id])
                return #delete the thread, dont update the ui even if
                       #a chunk is uploaded in the meantime.
                       
        #If I reach this point, the upload is complete and I have to save it to the history.
        d = {}
        if self.service in 'Dropbox':
            response = self.worker.finish('{}{}'.format(self.worker.remote, os.path.basename(self.worker.path)))
            path = response['path']
            #Get the share link
            url = self.worker.client.share(path)['url']
            d['name'] = os.path.basename(self.worker.path)
            date = str(datetime.datetime.now())
            d['date'] = date[:date.index('.')]
            d['path'] = path
            d['link'] = url
            self.logger.debug('Putting in queue.')
            self.out_queue.put(('add', self.service, self.id, d))
        elif self.service in 'GoogleDrive':
            b={'withLink':True, 'role':'reader', 'type':'anyone'}
            shareurl = 'https://docs.google.com/file/d/{}/edit?usp=sharing'
            r = self.worker.client.permissions().insert(fileId=self.worker.id, body=b).execute()
            d['name'] = os.path.basename(self.worker.path)
            date = str(datetime.datetime.now())
            d['date'] = date[:date.index('.')]
            d['path'] = self.worker.title
            d['link'] = shareurl.format(self.worker.id)
            self.logger.debug('Putting in queue.')
            self.out_queue.put(('add', self.service, self.id, d))
        return
