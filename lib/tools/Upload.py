import re
import os
from StringIO import StringIO
from UploadManager import LocalUploadManager

from dropbox import client, rest, session

def format_path(path):
    #Copied from client.py in dropbox api.
    """Normalize path for use with the Dropbox API.

    This function turns multiple adjacent slashes into single
    slashes, then ensures that there's a leading slash but
    not a trailing slash.
    """
    if not path:
        return path

    path = re.sub(r'/+', '/', path)

    if path == '/':
        return (u"" if isinstance(path, unicode) else "")
    else:
        return '/' + path.strip('/')

class DropboxUploader(object):
    #Copied from client.py in dropbox api.
    """Contains the logic around a chunked upload, which uploads a
    large file to Dropbox via the /chunked_upload endpoint
    """
    def __init__(self, file_obj, length, path, client=None):
        self.client = client
        self.offset = 0
        self.upload_id = None
        self.path = path

        self.last_block = None
        self.file_obj = file_obj
        self.target_length = length
    
    def set_client(self, client):
        self.client = client
        
    def file_obj_seek(self):
        self.file_obj.seek(self.offset)
    
    def upload_chunked(self, chunk_size = 4 * 1024 * 1024):
        """Uploads data from this ChunkedUploader's file_obj in chunks, until
        an error occurs. Throws an exception when an error occurs, and can
        be called again to resume the upload.

        Args:
            - ``chunk_size``: The number of bytes to put in each chunk. [default 4 MB]
        """

        while self.offset < self.target_length:
            next_chunk_size = min(chunk_size, self.target_length - self.offset)
            if self.last_block == None:
                self.last_block = self.file_obj.read(next_chunk_size)

            try:
                (self.offset, self.upload_id) = self.client.upload_chunk(StringIO(self.last_block), next_chunk_size, self.offset, self.upload_id)
                self.last_block = None
            except rest.ErrorResponse, e:
                reply = e.body
                if "offset" in reply and reply['offset'] != 0:
                    if reply['offset'] > self.offset:
                        self.last_block = None
                        self.offset = reply['offset']

    def finish(self, path, overwrite=False, parent_rev=None):
        """Commits the bytes uploaded by this ChunkedUploader to a file
        in the users dropbox.

        Args:
            - ``path``: The full path of the file in the Dropbox.
            - ``overwrite``: Whether to overwrite an existing file at the given path. [default False]
              If overwrite is False and a file already exists there, Dropbox
              will rename the upload to make sure it doesn't overwrite anything.
              You need to check the metadata returned for the new name.
              This field should only be True if your intent is to potentially
              clobber changes to a file that you don't know about.
            - ``parent_rev``: The rev field from the 'parent' of this upload. [optional]
              If your intent is to update the file at the given path, you should
              pass the parent_rev parameter set to the rev value from the most recent
              metadata you have of the existing file at that path. If the server
              has a more recent version of the file at the specified path, it will
              automatically rename your uploaded file, spinning off a conflict.
              Using this parameter effectively causes the overwrite parameter to be ignored.
              The file will always be overwritten if you send the most-recent parent_rev,
              and it will never be overwritten if you send a less-recent one.
        """

        path = "/commit_chunked_upload/%s%s" % (self.client.session.root, format_path(path))

        params = dict(
            overwrite = bool(overwrite),
            upload_id = self.upload_id
        )

        if parent_rev is not None:
            params['parent_rev'] = parent_rev

        url, params, headers = self.client.request(path, params, content_server=True)

        return self.client.rest_client.POST(url, params, headers)
        
class UploadQueue(object):
    def __init__(self, dbClient=None):
        self.pending_uploads = {}
        
        uploadManager = LocalUploadManager()
        uploadsFromFile = uploadManager.dropbox_get_uploads()
        
        for k,v in uploadsFromFile.items():
            #Check if the file still exists
            try:
                with open(v['path'],'r'):
                    pass
            except IOError:
                self.pending_uploads[k] = {'status':'Invalid path {}'.format(k), 'path':v['path']}
                continue
            
            fileSize = os.path.getsize(v['path'])
            
            dbUploader = DropboxUploader(open(v['path'],'rb'), fileSize, v['path'])
            dbUploader.offset = int(v['offset'])
            dbUploader.upload_id = None if v['upload_id'] == 'None' else v['upload_id']
            dbUploader.file_obj_seek()
            
            self.pending_uploads[k] = {'status':k, 'uploader':dbUploader}
    
    def add(self, path, length):
        dbUploader = None
        id = str(len(self.pending_uploads))
        try:
            dbUploader = DropboxUploader(open(path,'rb'), length, path)
        except IOError:
            self.pending_uploads[id] = {'status':'Invalid path {}'.format(id), 'path':path}
            return
        else:
            self.pending_uploads[id] = {'status':id, 'uploader':dbUploader}
    
    def delete(self, key):
        try:
            del(self.pending_uploads[key])
            uploadManager = LocalUploadManager()
            uploadManager.dropbox_delete_upload(key)
            #add it to history
        except KeyError:
            raise KeyError('No such key.')
    
    def remove_invalids(self):
        self.pending_uploads = {k:v for k,v in self.pending_uploads.items() if 'path' not in v}
    
    def dump(self):
        def create_dict(dbUploader):
            return {'upload_id':dbUploader.upload_id or 'None',
                    'offset':dbUploader.offset,
                    'path':dbUploader.path}
    
        uploadManager = LocalUploadManager()
        uploadManager.dropbox_flush_uploads()
        self.remove_invalids()
        
        uploadManager = LocalUploadManager()
        for v in self.pending_uploads.values():
            d = create_dict(v['uploader'])
            uploadManager.dropbox_update_upload(d['upload_id'], str(d['offset']), d['path'])