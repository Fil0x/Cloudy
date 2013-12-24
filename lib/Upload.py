import re
import os
import sys
import socket
import httplib2
from StringIO import StringIO

import local
import faults
from DataManager import LocalDataManager
from UploadManager import LocalUploadManager
from ApplicationManager import ApplicationManager

from kamaki.clients import ClientError
from dropbox import rest
from dropbox import client
from dropbox import session
from apiclient import errors
from simpleflake import simpleflake
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import Credentials
from oauth2client.client import AccessTokenRefreshError

#Pithos stuff
class PithosUploader(object):
    def __init__(self, path, remote='pithos', offset=0, client=None):
        self.client = client
        self.path = path
        self.remote = remote #Container
        self.offset = offset #Progress

        self.target_length = os.path.getsize(path)

    def upload_chunked(self, chunk_size=128*1024): #Chunk size unused.
        try:
            with open(self.path, 'rb') as f:
                try:
                    for i in self.client.upload_object(os.path.basename(self.path), f, public=True):
                        self.offset += i
                        try:
                            yield (float(self.offset)/self.target_length, self.path)
                        except ZeroDivisionError:
                            #The file was empty, it's 100% by default.
                            yield (1.0, self.path)
                except ClientError as e:
                    if e.status == 413: #Out of quota, http://tinyurl.com/pkmpuk6
                        yield (3, None)
                    elif e.status in [401, 404]:
                        yield (12, None)
                    elif 'Errno 11004' in e.message:
                        yield (22, None)
                    return
        except IOError as e:
            yield (2, None)
#End of Pithos stuff

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
    large file to Dropbox via the /chunked_upload endpoint.
    """
    def __init__(self, path, remote='/', offset=0, upload_id=None, client=None):
        self.client = client
        self.offset = offset
        self.upload_id = upload_id
        self.path = path
        self.remote = remote

        self.last_block = None
        self.target_length = os.path.getsize(path)

    def upload_chunked(self, chunk_size=128*1024):
        """Uploads data from this ChunkedUploader's file_obj in chunks, until
        an error occurs. Throws an exception when an error occurs, and can
        be called again to resume the upload.

        Args:
            - ``chunk_size``: The number of bytes to put in each chunk. [default 4 MB]
        """
        try:
            with open(self.path, 'rb') as file_obj:
                file_obj.seek(self.offset)
                while self.offset < self.target_length:
                    next_chunk_size = min(chunk_size, self.target_length - self.offset)
                    if self.last_block == None:
                        self.last_block = file_obj.read(next_chunk_size)

                    try:
                        (self.offset, self.upload_id) = self.client.upload_chunk(StringIO(self.last_block), next_chunk_size, self.offset, self.upload_id)
                        self.last_block = None
                        try:
                            yield (float(self.offset)/self.target_length, self.path)
                        except ZeroDivisionError:
                            #The file was empty, it's 100% by default.
                            yield (1.0, self.path)
                    except rest.ErrorResponse as e:
                        reply = e.body
                        if "offset" in reply and reply['offset'] != 0:
                            if reply['offset'] > self.offset:
                                self.last_block = None
                                self.offset = reply['offset']
                        if e.status == 507: #Out of quota, http://tinyurl.com/c62om2r
                            yield (3, None)
                        elif e.status == 404:
                            yield (12, None)
                        return
                    except rest.RESTSocketError as e:
                        yield (22, None)
                        return
        except IOError as e:
            yield (2, None)

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

    def __init__(self, path, remote='', parent_id='', offset=0, upload_uri=None, client=None):
        self.path = path
        body = {'title':os.path.basename(path)}
        if parent_id:
            body['parents'] = [{'id': parent_id}]
        self.body = body
        self.parent_id = parent_id
        self.offset = offset
        self.remote = remote
        self.target_length = os.path.getsize(path)
        self.upload_uri = upload_uri
        self.client = client
        #The variables below will be filled after the file has been uploaded.
        self.sharelink = None
        self.title = None

    def upload_chunked(self, chunk_size=256*1024):
        try:
            media_body = MediaFileUpload(self.path, chunksize=chunk_size, resumable=True)
            file = self.client.files().insert(body=self.body, media_body=media_body)
            file.resumable_progress = self.offset
            file.resumable_uri = self.upload_uri
            response = None
            while response is None:
                try:
                    status, response = file.next_chunk()
                    if status:
                        self.offset = file.resumable_progress
                        self.upload_uri = file.resumable_uri
                        yield (status.progress(), self.path)
                except AccessTokenRefreshError:
                    #https://developers.google.com/drive/handle-errors
                    self.offset = file.resumable_progress
                    self.upload_uri = file.resumable_uri
                    yield (12, None)
            if response:
                self.title = response['title']
                self.id = response['id']
                yield (1.0, self.path)
        #http://docs.python.org/2/library/errno.html
        except socket.error as e:
            yield(22, None)
        except IOError as e:
            yield (2, None)
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

        p = ApplicationManager()
        for s in p.get_services():
            getattr(self, '_{}_load'.format(s.lower()))()

    def _new_id(self):
        '''The identifier for each upload will be a random number
        generated by the simpleflake library.
        More information at: http://tinyurl.com/mqbjbpm
        '''
        return str(simpleflake())

    #initialization functions
    def _pithos_load(self):
        uploadManager = LocalUploadManager()
        uploadsFromFile = uploadManager.get_uploads('Pithos')

        for k,v in uploadsFromFile.iteritems():
            try:
                with open(v['path'], 'r'):
                    pass
            except IOError:
                self.pending_uploads['Pithos'][k] = {'error':'File not found',
                                                     'status':'Error-2',
                                                     'path':v['path']}
                continue

            if 'offset' not in v:
                self.pending_uploads['Pithos'][k] = {'error':'File not found',
                                                     'status':'Error-2',
                                                     'path':v['path']}
                continue

            offset = int(v['offset'])
            pithosUploader = PithosUploader(v['path'], v['destination'], offset)

            self.pending_uploads['Pithos'][k] = {'uploader':pithosUploader,
                                                 'status':v['status'],
                                                 'conflict':v['conflict']}

    def _dropbox_load(self):
        uploadManager = LocalUploadManager()
        uploadsFromFile = uploadManager.get_uploads('Dropbox')

        for k,v in uploadsFromFile.iteritems():
            try:
                with open(v['path'], 'r'):
                    pass
            except IOError:
                self.pending_uploads['Dropbox'][k] = {'error':'File not found',
                                                      'status':'Error-2',
                                                      'path':v['path']}
                continue

            if 'offset' not in v:
                self.pending_uploads['Dropbox'][k] = {'error':'File not found',
                                                          'status':'Error-2',
                                                          'path':v['path']}
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
                self.pending_uploads['GoogleDrive'][k] = {'error':'File not found',
                                                          'status':'Error-2',
                                                          'path':v['path']}
                continue

            if 'offset' not in v:
                self.pending_uploads['GoogleDrive'][k] = {'error':'File not found',
                                                          'status':'Error-2',
                                                          'path':v['path']}
                continue

            offset = int(v['offset'])
            upload_uri = None if v['upload_uri'] == 'None' else v['upload_uri']
            gdUploader = GoogleDriveUploader(v['path'], v['destination'], v['parent_id'], 
                                             offset, upload_uri)

            self.pending_uploads['GoogleDrive'][k] = {'uploader':gdUploader,
                                                      'status':v['status'],
                                                      'conflict':v['conflict']}
    #End of initialization funtions

    #Upload functions
    def add_from_error(self, service, id, path):
        uploader = getattr(sys.modules[__name__], '{}Uploader'.format(service))(path)
        self.pending_uploads[service][id] = {'uploader':uploader,
                                             'status':'Starting',
                                             'conflict':'KeepBoth'}
        return self.pending_uploads[service][id]

    def _normalize_state(self, state):
        if state in ['Starting', 'Running', 'Resuming']:
            return 'Starting'
        elif state in ['Paused', 'Pausing']:
            return 'Paused'
        elif 'Error' in state:
            return state

    def _pithos_add(self, path):
        id = self._new_id()
        uploader = None
        dm = LocalDataManager()
        try:
            uploader = PithosUploader(path, dm.get_service_root('Pithos'))
        except IOError:
            self.pending_uploads['Pithos'][id] = {'error':'File not found',
                                                  'status':'Error-2',
                                                  'path':path}
        else:
            self.pending_uploads['Pithos'][id] = {'uploader':uploader,
                                                  'status':'Starting',
                                                  'conflict':'KeepBoth'}
        return (id, self.pending_uploads['Pithos'][id])

    def _pithos_save(self):
        def create_dict(item):
            state = self._normalize_state(item['status'])
            return {'offset': str(item['uploader'].offset),
                    'path': item['uploader'].path,
                    'destination':item['uploader'].remote,
                    'status':state,
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.delete_upload('Pithos')

        for k, v in self.pending_uploads['Pithos'].iteritems():
            if v['status'] == 'Removing':
                continue #Dont save the uploads with Removing status.
            elif v['status'] == 'Error-2':
                ''' If the status is error-2 this can mean two things:
                    1)the upload raised this error in this app session,
                    2)the erroneous upload wasn't removed by the user
                     and it has lived at least one app session.
                '''
                if 'error' not in v: #1
                    uploadManager.add_upload('Pithos', k, **{'path':v['uploader'].path})
                else: #2
                    uploadManager.add_upload('Pithos', k, **{'path':v['path']})
            else:
                d = create_dict(v)
                uploadManager.add_upload('Pithos', k, **d)

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
            self.pending_uploads['Dropbox'][id] = {'error':'File not found',
                                                   'status':'Error-2',
                                                   'path':path}
        else:
            self.pending_uploads['Dropbox'][id] = {'uploader':uploader,
                                                   'status':'Starting',
                                                   'conflict':'KeepBoth'}
        return (id, self.pending_uploads['Dropbox'][id])

    def _dropbox_save(self):
        def create_dict(item):
            state = self._normalize_state(item['status'])
            return {'upload_id': item['uploader'].upload_id or 'None',
                    'offset': str(item['uploader'].offset),
                    'path': item['uploader'].path,
                    'destination':item['uploader'].remote,
                    'status':state,
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.delete_upload('Dropbox')

        for k, v in self.pending_uploads['Dropbox'].iteritems():
            if v['status'] == 'Removing':
                continue #Dont save the uploads with Removing status.
            elif v['status'] == 'Error-2':
                ''' If the status is error-2 this can mean two things:
                    1)the upload raised this error in this app session,
                    2)the erroneous upload wasn't removed by the user
                     and it has lived at least one app session.
                '''
                if 'error' not in v: #1
                    uploadManager.add_upload('Dropbox', k, **{'path':v['uploader'].path})
                else: #2
                    uploadManager.add_upload('Dropbox', k, **{'path':v['path']})
            else:
                d = create_dict(v)
                uploadManager.add_upload('Dropbox', k, **d)

    def _googledrive_add(self, path):
        id = self._new_id()
        uploader = None
        dm = LocalDataManager()
        try:
            with open(path, 'rb'):
                pass
            uploader = GoogleDriveUploader(path, dm.get_service_root('GoogleDrive'), 
                                           dm.get_folder_id())
        except IOError:
            self.pending_uploads['GoogleDrive'][id] = {'error':'File not found',
                                                       'status':'Error-2',
                                                       'path':path}
        else:
            self.pending_uploads['GoogleDrive'][id] = {'uploader':uploader,
                                                       'status':'Starting',
                                                       'conflict':'KeepBoth'}
        return (id, self.pending_uploads['GoogleDrive'][id])

    def _googledrive_save(self):
        def create_dict(item):
            state = self._normalize_state(item['status'])
            return {'upload_uri':item['uploader'].upload_uri or 'None',
                    'offset':item['uploader'].offset,
                    'path':item['uploader'].path,
                    'destination':item['uploader'].remote,
                    'parent_id':item['uploader'].parent_id, 
                    'status':state,
                    'conflict':item['conflict']}

        uploadManager = LocalUploadManager()
        uploadManager.delete_upload('GoogleDrive')

        for k, v in self.pending_uploads['GoogleDrive'].iteritems():
            if v['status'] == 'Removing':
                continue #Dont save the uploads with Removing status.
            elif v['status'] == 'Error-2':
                ''' If the status is error-2 this can mean two things:
                    1)the upload raised this error in this app session,
                    2)the erroneous upload wasn't removed by the user
                     and it has lived at least one app session.
                '''
                if 'error' not in v: #1
                    uploadManager.add_upload('GoogleDrive', k, **{'path':v['uploader'].path})
                else: #2
                    uploadManager.add_upload('GoogleDrive', k, **{'path':v['path']})
            else:
                d = create_dict(v)
                uploadManager.add_upload('GoogleDrive', k, **d)
    #end of Upload functions

    #History functions - exposed
    def add_history(self, service, id, **kwargs):
        ''' name=remote_filename, date=date, path=remote path, link=share_link '''
        upload_manager = LocalUploadManager()

        upload_manager.add_history(service, id, **kwargs)

    def get_history(self, service=None, id=None):
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

    def get_all_uploads(self):
        return self.pending_uploads

    def get(self, service, id):
        assert(id in self.pending_uploads[service])

        return self.pending_uploads[service][id]

    def save(self):
        p = ApplicationManager()
        for s in p.get_services():
            getattr(self, '_{}_save'.format(s.lower()))()

    def set_client(self, service, client):
        assert(service in local.services)

        for v in self.pending_uploads[service].values():
            v['uploader'].client = client

    def get_status(self, service, id):
        return self.pending_uploads[service][id]['status']

    def set_state(self, service, id, status):
        self.pending_uploads[service][id]['status'] = status
    #end of exposed functions
