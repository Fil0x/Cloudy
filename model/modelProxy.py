import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import threading
import logging
from PyQt4 import QtCore
import AppFacade
from model import Model
import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'
    threadDict = {} 
    
    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.model = Model()
        self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def detailed_view_data(self):
        data = []
        for service, items in self.model.uploadQueue.pending_uploads.iteritems():
            for key, d in items.iteritems():
                if len(d):
                    name = os.path.basename(d['uploader'].path)
                    progress = round(float(d['uploader'].offset)/d['uploader'].target_length, 2)
                    data.append([name, service, d['destination'], d['status'],
                              progress, d['conflict'], 'Not ready', key])
                          
        return data
    
    def start_uploads(self):
        pass
        
    def dropbox_add(self, path):
        self.model.uploadQueue.dropbox_add(path)

        self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def googledrive_add(self, path, body={}):
        self.model.uploadQueue.googledrive_add(path, body)

        self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def dump(self):
        self.model.uploadQueue.dump()

    def delete(self, service, key):
        self.model.uploadQueue.delete(service, key)

        self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uploadQueue)

    class UploadThread(threading.Thread):
        
        def __init__(self, uploader, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
                 
            threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
            self.args = args
            self.kwargs = kwargs
            self.worker = uploader #Uploader already has a validated client.
            self.state = -1 #It can be 0 to stop when the next chunk is uploaded
                            #or 1 to delete the upload.

        def run(self):
            for i in self.worker.upload_chunked():
                if self.state == 0:
                    return #send signal to UI
                elif self.state == 1:
                    return #delete the thread, dont update the ui even if 
                           #a chunk is uploaded in the meantime.
            
            if type(self.worker) is DropboxUploader:
                self.worker.finish('/new.pdf') #change path
            return 