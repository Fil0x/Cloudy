import re
import os
import time
import md5
import httplib2
import requests
import mimetypes
from StringIO import StringIO
from simpleflake import simpleflake
from UploadManager import LocalUploadManager

from dropbox import rest
from dropbox import client
from dropbox import session
from oauth2client.client import Credentials
from apiclient import errors
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient.http import DEFAULT_CHUNK_SIZE

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
    """Contains the logic around a chunked upload, which uploads a
    large file to Dropbox via the /chunked_upload endpoint
    """
    def __init__(self, path, offset=0, upload_id=None, client=None):
        self.client = client
        self.offset = offset
        self.upload_id = upload_id
        self.path = path

        self.last_block = None
        self.file_obj = open(path, 'rb')
        self.target_length = os.path.getsize(path)

        self.file_obj.seek(self.offset)

    def set_client(self, c):
        self.client = c

    def upload_chunked(self, chunk_size = 1024 * 1024):
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
                yield float(self.offset)/self.target_length
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
    def __init__(self, path, body, offset, upload_uri, client=None):
        self.path = path
        self.body = body
        self.offset = offset
        self.target_length = os.path.getsize(path)
        self.upload_uri = upload_uri
        self.client = None

    def set_client(self, client):
        self.client = client

    def upload_chunked(self, chunk_size=DEFAULT_CHUNK_SIZE):
        media_body = MediaFileUpload(self.path, chunksize=DEFAULT_CHUNK_SIZE, resumable=True)
        file = self.client.files().insert(body=self.body, media_body=media_body)
        file.resumable_progress = self.offset
        file.resumable_uri = self.upload_uri
        response = None
        while response is None:
            try:
                status, response = file.next_chunk()
                if status:
                    print "Upload %d%% complete." % int(status.progress() * 100)
            except Exception:
                print 'Something happened'
                self.offset = file.resumable_progress
                self.upload_uri = file.resumable_uri
        #Error handle
#End GoogleDrive stuff

class UploadQueue(object):
    def __init__(self):
        self.pending_uploads = {}
        for service in LocalUploadManager.services:
            self.pending_uploads[service] = {}

        self._dropbox_load()
        self._googledrive_load()

    def _dropbox_load(self):
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
            dbUploader = DropboxUploader(path, offset, upload_id)

            self.pending_uploads['Dropbox'][k] = {'uploader':dbUploader,
                                                  'destination':v['destination'],
                                                  'status':v['status'],
                                                  'conflict':v['conflict']}

    def _new_id(self):
        '''The identifier for each upload will be a random number
        generated by the simpleflake library.
        More information at: http://tinyurl.com/mqbjbpm
        '''
        return simpleflake()

    def dropbox_add(self, path):
        '''
        path: localpath to the file.
        The identifier for each upload will be a md5 hash of the local path
        of the file to be uploaded plus the seconds since the epoch.
        This guarantees that the hash will be unique if the user decides to 
        add the same file twice.
        '''
        id = self._new_id()
        dbUploader = None
        try:
            dbUploader = DropboxUploader(path)
        except IOError:
            self.pending_uploads['Dropbox'][id] = {'error':'Invalid path', 
                                                   'path':path}
        else:
            self.pending_uploads['Dropbox'][id] = {'uploader':dbUploader,
                                                   'destination':'/',
                                                   'status':'Running',
                                                   'conflict':'KeepBoth'}

    def _dropbox_dump(self):
        def create_dict(item):
            return {'upload_id': item['uploader'].upload_id or 'None',
                    'offset': str(item['uploader'].offset),
                    'path': item['uploader'].path,
                    'destination':item['destination'],
                    'status':item['status'],
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.flush_uploads('Dropbox')
        self._remove_invalids('Dropbox')

        for k, v in self.pending_uploads['Dropbox'].iteritems():
            d = create_dict(v)
            uploadManager.dropbox_update_upload(k, **d)

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
            gdUploader = GoogleDriveUploader(v['path'], {'title':os.path.basename(v['path'])},
                                             offset, upload_uri)

            self.pending_uploads['GoogleDrive'][k] = {'uploader':gdUploader,
                                                      'destination':v['destination'],
                                                      'status':v['status'],
                                                      'conflict':v['conflict']}

    def googledrive_add(self, path, body={}):
        id = self._new_id()
        gdUploader = None
        try:
            with open(path, 'rb'):
                pass
            filesize = os.path.getsize(path)
            gdUploader = GoogleDriveUploader(path, body, 0, None)
        except IOError:
            self.pending_uploads['GoogleDrive'][id] = {'error':'Invalid path', 
                                                       'path':path}
        else:
            self.pending_uploads['GoogleDrive'][id] = {'uploader':gdUploader,
                                                       'destination':'/',
                                                       'status':'Running',
                                                       'conflict':'KeepBoth'}

    def _googledrive_dump(self):
        def create_dict(item):
            return {'upload_uri':item['uploader'].resumable_uri or 'None',
                    'offset':item['uploader'].resumable_progress,
                    'path':item['uploader'].path,
                    'destination':item['destination'],
                    'status':item['status'],
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.flush_uploads('GoogleDrive')
        self._remove_invalids('GoogleDrive')

        for k, v in self.pending_uploads['GoogleDrive'].iteritems():
            d = create_dict(v)
            uploadManager.googledrive_update_upload(k, **d)

    def _remove_invalids(self, s):
        self.pending_uploads[s] = {k:v for k,v in self.pending_uploads[s].items() if 'error' not in v}

    def delete(self, service, key):
        try:
            del(self.pending_uploads[service][key])
        except KeyError:
            raise KeyError('No such key.')

    def dump(self):
        self._dropbox_dump()
        self._googledrive_dump()

    def set_client(self, service, client):
        assert(service in services)
    
        for v in self.pending_uploads[service].values():
            v['uploader'].set_client(client)

    def set_state(self, service, key, state):
        self.pending_uploads[service][key]['status'] = state