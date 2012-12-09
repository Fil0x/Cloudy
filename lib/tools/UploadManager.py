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
    def dropbox_update_upload(self, offset, upload_id, path):
        self.upload['Dropbox'][upload_id] = {}
        self.upload['Dropbox'][upload_id]['offset'] = offset or self.upload['Dropbox'][upload_id]['offset']
        self.upload['Dropbox'][upload_id]['path'] = path or self.upload['Dropbox'][upload_id]['path']
        
        self.upload.write()
    
    def dropbox_delete_upload(self, upload_id):
        try:
            del(self.upload['Dropbox'][upload_id])
            
            self.upload.write()
        except KeyError:
            raise KeyError('Upload_id:{} not found.'.format(upload_id))