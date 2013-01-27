import json
import os.path
from configobj import ConfigObj

def checkUpload(f):
    def wrapper(*args):
        try:
            with open(args[0].uploadPath,'r'):
                pass
        except IOError:
            args[0]._create_file(args[0].uploadPath, 'upload')
        return f(*args)
    return wrapper

def checkHistory(f):
    def wrapper(*args):
        try:
            with open(args[0].historyPath,'r'):
                pass
        except IOError:
            args[0]._create_file(args[0].historyPath, 'history')
        return f(*args)
    return wrapper
    
class UploadManager(object):
    basepath = os.path.join(os.path.dirname(os.getcwd()), 'Configuration')
    services = ['Dropbox', 'Pithos', 'Skydrive', 'GoogleDrive']
    
class LocalUploadManager(UploadManager):
    def __init__(self, historyName='history.ini', uploadName='upload.ini'):
        self.historyPath = os.path.join(self.basepath,historyName)
        self.uploadPath = os.path.join(self.basepath,uploadName)

        for path,attr in [(self.historyPath, 'history'),
                          (self.uploadPath, 'upload')]:
            try:
                with open(path,'r'):
                    pass
            except IOError:
                self._create_file(path, attr)
                
        self.history = ConfigObj(self.historyPath)
        self.upload = ConfigObj(self.uploadPath)
         
    def _create_file(self, path, attr):
        config = ConfigObj(path)
        
        config['Dropbox'] = {}
        config['Pithos'] = {}
        config['Skydrive'] = {}
        config['GoogleDrive'] = {}
        
        config.write()

        setattr(self, attr, config)
    
    @checkUpload
    def dropbox_update_upload(self, upload_id, offset, path):
        id = str(len(self.upload['Dropbox']))
        
        self.upload['Dropbox'][id] = {}
        self.upload['Dropbox'][id]['upload_id'] = upload_id or self.upload['Dropbox'][id]['upload_id']
        self.upload['Dropbox'][id]['offset'] = offset or self.upload['Dropbox'][id]['offset']
        self.upload['Dropbox'][id]['path'] = path or self.upload['Dropbox'][id]['path']
        
        self.upload.write()

    @checkUpload
    def googledrive_update_upload(self, upload_uri, offset, path):
        id = str(len(self.upload['GoogleDrive']))
        
        self.upload['GoogleDrive'][id] = {}
        self.upload['GoogleDrive'][id]['upload_uri'] = upload_uri or self.upload['GoogleDrive'][id]['upload_uri']
        self.upload['GoogleDrive'][id]['path'] = path or self.upload['GoogleDrive'][id]['path']
        self.upload['GoogleDrive'][id]['offset'] = offset or self.upload['GoogleDrive'][id]['offset']
        
        self.upload.write()        
   
    @checkUpload
    def get_uploads(self, service):
        assert(service in self.services)
        
        return self.upload[service]
    
    def delete_upload(self, service, id):
        assert(service in self.services)
        
        def delete_item(i):
            try:
                del(self.upload[service][i])
            except KeyError:
                pass
        
        if isinstance(id,list):
            map(delete_item, id)
        else:
            del(self.upload[service][id])
        
        self.upload.write()

    def flush_uploads(self, service):
        assert(service in self.services)
        
        self.upload[service] = {}
        
        self.upload.write()