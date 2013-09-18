import httplib2

from DataManager import LocalDataManager
import errors

#from pithos.tools.lib.client import Pithos_Client, Fault - Deprecated(?)
from dropbox.client import DropboxClient
from dropbox import rest
from oauth2client.client import Credentials
from apiclient.discovery import build


class AuthManager(object):
    def __init__(self):
        self.dataManager = LocalDataManager()

    def pithos_authentication(self):
        pass

    def pithos_add_user(self, user, url, token):
        pass
        
    def dropbox_authentication(self):
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
    def googledrive_authentication(self):
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