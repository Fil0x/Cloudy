import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import inspect

import logger

from configobj import ConfigObj


def checkFile(fileType):
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


class UploadManager(object):
    filedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    basepath =  os.path.join(os.path.dirname(filedir), 'Configuration')
    services = ['Dropbox', 'Pithos', 'GoogleDrive']


class LocalUploadManager(UploadManager):
    def __init__(self, historyName='history.ini', uploadName='upload.ini'):
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

        config['Dropbox'] = {}
        config['Pithos'] = {}
        config['GoogleDrive'] = {}

        config.write()

        setattr(self, attr, config)

    @checkFile('uploadPath')
    def dropbox_update_upload(self, id, **kwargs):
        self.upload['Dropbox'].setdefault(id, kwargs)

        self.upload.write()

    @checkFile('uploadPath')
    def googledrive_update_upload(self, id, **kwargs):
        self.upload['GoogleDrive'].setdefault(id, kwargs)

        self.upload.write()

    @checkFile('uploadPath')
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
                    logger.logger_factory('get_uploads').debug('Key:{}'.format(i))
        return r

    def delete_upload(self, service, id):
        assert(service in self.services)

        def delete_item(i):
            try:
                del(self.upload[service][i])
            except KeyError:
                logger.logger_factory('delete_upload').debug('Key:{}'.format(i))

        if isinstance(id,list):
            map(delete_item, id)
        else:
            del(self.upload[service][id])

        self.upload.write()

    def flush_uploads(self, service):
        assert(service in self.services)

        self.upload[service] = {}

        self.upload.write()