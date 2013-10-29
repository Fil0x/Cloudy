import json
import httplib2

import local
import faults
from DataManager import Manager
from DataManager import LocalDataManager

from dropbox import rest
from dropbox.client import DropboxClient
from dropbox.client import DropboxOAuth2FlowNoRedirect
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import AccessTokenRefreshError

class AuthManager(Manager):
    def __init__(self):
        self.auth_functions = [self._dropbox_auth,
                               self._pithos_auth,
                               self._googledrive_auth]
        self.service_auth = dict(zip(self.services, self.auth_functions))

        self.add_functions = [self._dropbox_add_user,
                              self._pithos_add_user,
                              self._googledrive_add_user]
        self.add_user = dict(zip(self.services, self.add_functions))

    #exposed functions
    def authenticate(self, service):
        assert(service in self.services)

        return self.service_auth[service]()

    #TODO: pithos
    def add_and_authenticate(self, service, key):
        assert(service in self.services)

        return self.add_user[service](key)
    #end of exposed functions

    def _pithos_auth(self):
        pass

    def _pithos_add_user(self, user, url, token):
        pass

    #https://www.dropbox.com/developers/core/docs/error handling
    def _dropbox_auth(self):
        access_token = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        access_token = dataManager.get_dropbox_token()

        dropboxClient = DropboxClient(access_token)

        try:
            dropboxClient.account_info()
        except rest.ErrorResponse as e:
            if e.status == 401:
                raise faults.InvalidAuth('Dropbox-Auth')
        except rest.RESTSocketError as e:
            raise faults.NetworkError('No internet-Auth')

        return dropboxClient

    def _dropbox_add_user(self, key):
        dataManager = LocalDataManager()
        dataManager.add_dropbox_token(key)
        return self._dropbox_auth()

    #http://tinyurl.com/kdv3ttb
    def _googledrive_auth(self):
        credentials = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        credentials = dataManager.get_googledrive_credentials()

        credentials = Credentials.new_from_json(credentials)
        http = credentials.authorize(httplib2.Http())
        drive_service = build('drive', 'v2', http=http)

        try:
            drive_service.about().get().execute()
        except errors.HttpError as e:
            raise
        except AccessTokenRefreshError:
            raise faults.InvalidAuth('GoogleDrive')
            #raise faults.NetworkError('No internet.')

        dataManager.set_googledrive_credentials(credentials)
        return drive_service

    def _googledrive_add_user(self, credentials):
        dataManager = LocalDataManager()
        dataManager.set_googledrive_credentials(credentials)
        return self._googledrive_auth()

    def get_dropbox_flow(self):
        return DropboxOAuth2FlowNoRedirect(local.Dropbox_APPKEY,
                                           local.Dropbox_APPSECRET)
                                           
    def get_googledrive_flow(self):
        return OAuth2WebServerFlow(local.GoogleDrive_APPKEY, local.GoogleDrive_APPSECRET,
                                   local.GoogleDrive_OAUTHSCOPE, local.GoogleDrive_REDIRECTURI)