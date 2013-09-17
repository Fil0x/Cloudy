import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import threading

import AppFacade
import lib.Upload
from model import Model
import logger

from PyQt4 import QtCore
import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.active_threads = {}
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
    #TODO: I need the root beforehand.
    def __init__(self, uploader, **kwargs):

        threading.Thread.__init__(self, **kwargs)
        self.worker = uploader #Uploader already has a validated client.
        self._state = 0 #It can be 1 to stop when the next chunk is uploaded
                        #or 2 to delete the upload.

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        assert(value in range(3))

        self._state = value

    def run(self):
        l = logger.logger_factory(self.__class__.__name__)
        for i in self.worker.upload_chunked():
            l.debug('Uploaded:{}'.format(i))
            if self._state == 1:
                l.debug('Paused with {}'.format(i))
                return #send signal to UI
            elif self.state == 2:
                return #delete the thread, dont update the ui even if
                       #a chunk is uploaded in the meantime.

        if type(self.worker) is lib.Upload.DropboxUploader:
            self.worker.finish('{}{}'.format(self.worker.remote, os.path.basename(self.worker.path)))
        return
            