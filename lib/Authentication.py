import httplib2

import errors
from DataManager import Manager
from DataManager import LocalDataManager

#from pithos.tools.lib.client import Pithos_Client, Fault - Deprecated(?)
from dropbox.client import DropboxClient
from dropbox import rest
from oauth2client.client import Credentials
from apiclient.discovery import build


class AuthManager(Manager):
    def __init__(self):
        self.dataManager = LocalDataManager()
        self.auth_functions = [self._dropbox_auth, 
                               self._pithos_auth, 
                               self._googledrive_auth]         
        
        self.service_auth = dict(zip(self.services, self.auth_functions))
    
    def authenticate(self, service):
        '''Use this function to get a service client.
           params:
           service: one of the following 'Dropbox', 'Pithos', 'GoogleDrive'.
        '''
        assert(service in self.services)
        
        return self.service_auth[service]()
        
    def _pithos_auth(self):
        pass

    def pithos_add_user(self, user, url, token):
        pass
        
    def _dropbox_auth(self):
        access_token = None
        self.dataManager.update()

        #A KeyError will be raised if there is no token.
        access_token = self.dataManager.get_dropbox_token()

        dropboxClient = DropboxClient(access_token)

        try:
            dropboxClient.account_info()
        except rest.ErrorResponse as e:
            #The token is invalid.
            raise errors.InvalidAuth('Dropbox token is invalid')
        except rest.RESTSocketError as e:
            #No internet.
            return None

        return dropboxClient

    def dropbox_add_user(self, key):
        self.dataManager.add_dropbox_token(key)
        return self.dropboxAuthentication()

    #http://tinyurl.com/kdv3ttb
    def _googledrive_auth(self):
        credentials = None
        self.dataManager.update()

        #A KeyError will be raised if there is no token.
        credentials = self.dataManager.get_googledrive_credentials()

        credentials = Credentials.new_from_json(credentials)
        http = credentials.authorize(httplib2.Http())
        drive_service = build('drive', 'v2', http=http)
        file = drive_service.files().list()

        try:
            file.execute()
        except Exception as e:
            raise e #dunno..

        self.dataManager.set_googledrive_credentials(credentials)
        return drive_service

    def googledrive_add_user(self, credentials):
        self.dataManager.update_googledrive_credentials(credentials)
        return self.googledriveAuthentication()
