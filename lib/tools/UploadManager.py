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
    basepath = os.path.join(os.getcwd(), 'Configuration')
    
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
    def dropbox_get_uploads(self):
        return self.upload['Dropbox']
    
    @checkUpload
    def dropbox_update_upload(self, upload_id, offset, path):
        id = str(len(self.upload['Dropbox']))
        
        self.upload['Dropbox'][id] = {}
        self.upload['Dropbox'][id]['upload_id'] = upload_id or self.upload['Dropbox'][id]['upload_id']
        self.upload['Dropbox'][id]['offset'] = offset or self.upload['Dropbox'][id]['offset']
        self.upload['Dropbox'][id]['path'] = path or self.upload['Dropbox'][id]['path']
        
        self.upload.write()
    
    def dropbox_delete_upload(self, id):
        def delete_item(i):
            try:
                del(self.upload['Dropbox'][i])
            except KeyError:
                pass
        
        if isinstance(id,list):
            map(delete_item, id)
        else:
            del(self.upload['Dropbox'][id])
        
        self.upload.write()
    
    def dropbox_flush_uploads(self):
        self.upload['Dropbox'] = {}