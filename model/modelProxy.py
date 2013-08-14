import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
from PyQt4 import QtCore
import AppFacade
from model import Model
import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'
    threadQueue = []
    
    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.model = Model()
        self.sendNotification(AppFacade.AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def detailed_view_data(self):
        '''
        This will be called each time the detailedWindow receives a signal
        that it has to refresh its data.
        '''
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
        dropboxClient = self.model.authManager.dropboxAuthentication()
        googledriveClient = self.model.authManager.googledriveAuthentication()
        
        self.model.uploadQueue.set_client('Dropbox', dropboxClient)
        self.model.uploadQueue.set_client('GoogleDrive', googledriveClient)
        
        for k, v in self.model.uploadQueue.pending_uploads.iteritems():
            for item in v.values():
                if item['status'] == 'Running':
                    self.threadQueue.append(UploadWorker(item))
                    self.threadQueue[-1].start()
    
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


class UploadWorker(QtCore.QThread):

    def __init__(self, item):
        QtCore.QThread.__init__(self)

        self.item = item

    def run(self):
        uploader = self.item['uploader']
        dest = self.item['destination']

        for progress in uploader.upload_chunked():
            print '{}:{}'.format(uploader.path, progress)
        uploader.finish(dest + os.path.basename(uploader.path))