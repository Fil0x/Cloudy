import sys
if ".." not in sys.path:
    sys.path.append("..")

import os

import logger
from DataManager import Manager

from configobj import ConfigObj


def check_file(fileType):
    def fdec(func):
        def f(*args, **kwargs):
            path = getattr(args[0], fileType)
            try:
                with open(path, 'r'):
                    pass
            except IOError:
                args[0]._create_file(path, fileType)
            return func(*args, **kwargs)
        return f
    return fdec


class LocalUploadManager(Manager):
    def __init__(self, historyName='history.ini', uploadName='upload.ini'):
        self.logger = logger.logger_factory(self.__class__.__name__)

        self.historyPath = os.path.join(self.basepath, historyName)
        self.uploadPath = os.path.join(self.basepath, uploadName)

        for path, attr in [(self.historyPath, 'history'),
                          (self.uploadPath, 'upload')]:
            try:
                with open(path, 'r'):
                    pass
            except IOError:
                self._create_file(path, attr)

        self.history = ConfigObj(self.historyPath)
        self.upload = ConfigObj(self.uploadPath)

    def _create_file(self, path, attr):
        config = ConfigObj(path)

        for s in self.services:
            config[s] = {}

        config.write()

        setattr(self, attr, config)

    #upload functions
    @check_file('uploadPath')
    def add_upload(self, service, id, **kwargs):
        assert(service in self.services)

        self.upload[service].setdefault(id, kwargs)

        self.upload.write()

    @check_file('uploadPath')
    def get_uploads(self, service, id=None):
        '''id: None to get all the uploads, list of the upload ids that you want'''
        assert(service in self.services)

        r = {}
        if not id:
            r = self.upload[service]
        elif isinstance(id, list):
            for i in id:
                try:
                    r[i] = self.upload[service][i]
                except KeyError:
                    #It should never appear.
                    self.logger.debug('Key(get, upload):{}'.format(i))
        return r

    def delete_upload(self, service, id=None):
        assert(service in self.services)

        def delete_item(i):
            try:
                del(self.upload[service][i])
            except KeyError:
                self.logger.debug('Key(delete):{}'.format(i))

        if not id:
            self.upload[service] = {}
        elif isinstance(id,list):
            map(delete_item, id)
        else:
            del(self.upload[service][id])

        self.upload.write()
    #End of upload functions

    #history functions
    @check_file('historyPath')
    def add_history(self, service, id, **kwargs):
        ''' remote filename, remote path, date & time, share link '''
        assert(service in self.services)

        if id in self.history[service]:
            del self.history[service][id]
        self.history[service].setdefault(id, kwargs)
        d = str(kwargs['date'])
        self.history[service][id]['date'] = d[:d.index('.')]

        self.history.write()

    @check_file('historyPath')
    def get_history(self, service=None, id=None):
        ''' id=list '''
        if not service:
            return self.history.dict()
        
        assert(service in self.services)

        r = {}
        if not id:
            r = self.history[service]
        elif isinstance(id, list):
            for i in id:
                try:
                    r[i] = self.history[service][i]
                except KeyError:
                    #It should never appear.
                    self.logger.debug('Key(get, history):{}'.format(i))
        return r

    def delete_history(self, service, id=None):
        assert(service in self.services)

        def delete_item(i):
            try:
                del(self.history[service][i])
            except KeyError:
                self.logger.debug('Key(delete, history):{}'.format(i))

        if not id:
            self.history[service] = {}
        elif isinstance(id,list):
            map(delete_item, id)
        else:
            del(self.history[service][id])

        self.history.write()
    #end of history functions
