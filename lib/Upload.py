import re
import os
import httplib2
from StringIO import StringIO

import local
from DataManager import LocalDataManager
from UploadManager import LocalUploadManager

from dropbox import rest
from dropbox import client
from dropbox import session
from apiclient import errors
from simpleflake import simpleflake
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import Credentials

#Dropbox stuff
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
    #Crashes if target_length is 0.
    """Contains the logic around a chunked upload, which uploads a
    large file to Dropbox via the /chunked_upload endpoint.
    """
    def __init__(self, path, remote='/', offset=0, upload_id=None, client=None):
        self.client = client
        self.offset = offset
        self.upload_id = upload_id
        self.path = path
        self.remote = remote

        self.last_block = None
        self.file_obj = open(path, 'rb')
        self.target_length = os.path.getsize(path)

        self.file_obj.seek(self.offset)

    def upload_chunked(self, chunk_size=128*1024):
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
                yield (float(self.offset)/self.target_length, self.path, self.upload_id, self.offset)
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
#End Dropbox stuff

#GoogleDrive stuff
class GoogleDriveUploader(object):

    def __init__(self, path, remote='', offset=0, upload_uri=None, client=None):
        self.path = path
        self.body = {'title':os.path.basename(path)}
        self.offset = offset
        self.remote = remote
        self.target_length = os.path.getsize(path)
        self.upload_uri = upload_uri
        self.client = client
        #These variables will be filled after the file has been uploaded.
        self.sharelink = None
        self.title = None

    def upload_chunked(self, chunk_size=256*1024):
        media_body = MediaFileUpload(self.path, chunksize=chunk_size, resumable=True)
        file = self.client.files().insert(body=self.body, media_body=media_body)
        file.resumable_progress = self.offset
        file.resumable_uri = self.upload_uri
        response = None
        while response is None:
            try:
                status, response = file.next_chunk()
                if status:
                    yield (status.progress(), self.path, self.upload_uri, self.offset)
            except Exception:
                print 'Something happened'
                self.offset = file.resumable_progress
                self.upload_uri = file.resumable_uri
        #Error handle
        self.sharelink = response['alternateLink']
        self.title = response['title']
#End GoogleDrive stuff

class UploadQueue(object):
    ''' The purpose of this class is to keep all the information
        about the files that have been stopped or running.
        The delete ones are removed immediately from this list.
    '''
    def __init__(self):
        self.pending_uploads = {}
        for service in local.services:
            self.pending_uploads[service] = {}

        self._dropbox_load()
        self._googledrive_load()

    def _new_id(self):
        '''The identifier for each upload will be a random number
        generated by the simpleflake library.
        More information at: http://tinyurl.com/mqbjbpm
        '''
        return str(simpleflake())

    #initialization functions
    def _dropbox_load(self):
        #Function called on initialization
        uploadManager = LocalUploadManager()
        uploadsFromFile = uploadManager.get_uploads('Dropbox')

        for k,v in uploadsFromFile.iteritems():
            try:
                with open(v['path'], 'r'):
                    pass
            except IOError:
                self.pending_uploads['Dropbox'][k] = {'error':'Invalid path', 'path':v['path']}
                continue

            offset = int(v['offset'])
            upload_id = None if v['upload_id'] == 'None' else v['upload_id']
            dbUploader = DropboxUploader(v['path'], v['destination'], offset, upload_id)

            self.pending_uploads['Dropbox'][k] = {'uploader':dbUploader,
                                                  'status':v['status'],
                                                  'conflict':v['conflict']}

    def _googledrive_load(self):
        uploadManager = LocalUploadManager()
        uploadsFromFile = uploadManager.get_uploads('GoogleDrive')

        for k, v in uploadsFromFile.items():
            #Check if the file still exists
            try:
                with open(v['path'],'r'):
                    pass
            except IOError:
                self.pending_uploads['GoogleDrive'][k] = {'status':'Invalid path {}'.format(k), 'path':v['path']}
                continue

            offset = int(v['offset'])
            upload_uri = None if v['upload_uri'] == 'None' else v['upload_uri']
            gdUploader = GoogleDriveUploader(v['path'], v['destination'], offset, upload_uri)

            self.pending_uploads['GoogleDrive'][k] = {'uploader':gdUploader,
                                                      'status':v['status'],
                                                      'conflict':v['conflict']}

    #End of initialization funtions

    #Upload functions
    def _dropbox_add(self, path):
        '''
        path: localpath to the file.
        The identifier for each upload will be an id generated by simpleflake.
        '''
        id = self._new_id()
        uploader = None
        dm = LocalDataManager()
        try:
            uploader = DropboxUploader(path, dm.get_service_root('Dropbox'))
        except IOError:
            self.pending_uploads['Dropbox'][id] = {'error':'Invalid path',
                                                   'path':path}
        else:
            self.pending_uploads['Dropbox'][id] = {'uploader':uploader,
                                                   'status':'Running',
                                                   'conflict':'KeepBoth'}
        return (id, self.pending_uploads['Dropbox'][id])

    def _dropbox_save(self):
        def create_dict(item):
            return {'upload_id': item['uploader'].upload_id or 'None',
                    'offset': str(item['uploader'].offset),
                    'path': item['uploader'].path,
                    'destination':item['uploader'].remote,
                    'status':item['status'],
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.delete_upload('Dropbox')
        self._remove_invalids('Dropbox')

        for k, v in self.pending_uploads['Dropbox'].iteritems():
            d = create_dict(v)
            uploadManager.add_upload('Dropbox', k, **d)

    def _googledrive_add(self, path):
        id = self._new_id()
        uploader = None
        dm = LocalDataManager()
        try:
            with open(path, 'rb'):
                pass
            uploader = GoogleDriveUploader(path, dm.get_service_root('GoogleDrive'))
        except IOError:
            self.pending_uploads['GoogleDrive'][id] = {'error':'Invalid path',
                                                       'path':path}
        else:
            self.pending_uploads['GoogleDrive'][id] = {'uploader':uploader,
                                                       'status':'Running',
                                                       'conflict':'KeepBoth'}
        return (id, self.pending_uploads['GoogleDrive'][id])

    def _googledrive_save(self):
        def create_dict(item):
            return {'upload_uri':item['uploader'].resumable_uri or 'None',
                    'offset':item['uploader'].resumable_progress,
                    'path':item['uploader'].path,
                    'destination':item['uploader'].remote,
                    'status':item['status'],
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.delete_upload('GoogleDrive')
        self._remove_invalids('GoogleDrive')

        for k, v in self.pending_uploads['GoogleDrive'].iteritems():
            d = create_dict(v)
            uploadManager.add_upload('GoogleDrive', k, **d)

    def _remove_invalids(self, s):
        self.pending_uploads[s] = {k:v for k,v in self.pending_uploads[s].items() if 'error' not in v}
    #end of Upload functions
    
    #History functions - exposed
    def add_history(self, service, id, **kwargs):
        ''' name=remote_filename, date=date, path=remote path, link=share_link '''
        upload_manager = LocalUploadManager()
        
        upload_manager.add_history(service, id, **kwargs)

    def get_history(self, service, id=None):
        upload_manager = LocalUploadManager()
        
        return upload_manager.get_history(service, id)
        
    def delete_history(self, service, id=None):
        upload_manager = LocalUploadManager()
        
        upload_manager.delete_history(service, id)
        
    #end of History functions
    
    #Exposed functions.
    def add(self, service, path):
        return getattr(self, '_{}_add'.format(service.lower()))(path)

    def delete(self, service, id):
        try:
            del(self.pending_uploads[service][id])
        except KeyError:
            raise KeyError('No such key.')

    def get_running(self, service=''):
        r = {}
        if service:
            assert(service in local.services)
            r[service] = {}
            for k, v in self.pending_uploads[service].iteritems():
                if 'error' not in v and v['status'] == 'Running':
                    r[service][k] = v
        else:
            for s, v in self.pending_uploads.iteritems():
                r[s] = {}
                for id, data in v.iteritems():
                    if 'error' not in data and data['status'] == 'Running':
                        r[s][id] = data

        return r

    def get(self, service, id):
        assert(id in self.pending_uploads[service])

        return self.pending_uploads[service][id]

    def save(self):
        self._dropbox_save()
        self._googledrive_save()

    def set_client(self, service, client):
        assert(service in local.services)

        for v in self.pending_uploads[service].values():
            v['uploader'].client = client

    def set_state(self, service, id, status):
        self.pending_uploads[service][id]['status'] = status
    #end of exposed functions
