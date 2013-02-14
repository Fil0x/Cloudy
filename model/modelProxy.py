import sys
if ".." not in sys.path:
    sys.path.append("..")

from model import Model
import puremvc.patterns.proxy
from AppFacade import AppFacade


class ModelProxy(puremvc.patterns.proxy.Proxy):
    NAME = 'MODELPROXY'

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.model = Model()
        self.sendNotification(AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def dropbox_add(self, path):
        self.model.uploadQueue.dropbox_add(path)

        self.sendNotification(AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def googledrive_add(self, path, body={}):
        self.model.uploadQueue.googledrive_add(path, body)

        self.sendNotification(AppFacade.DATA_CHANGED, self.model.uploadQueue)

    def dump(self):
        self.model.uploadQueue.dump()

    def delete(self, service, key):
        self.model.uploadQueue.delete(service, key)

        self.sendNotification(AppFacade.DATA_CHANGED, self.model.uploadQueue)