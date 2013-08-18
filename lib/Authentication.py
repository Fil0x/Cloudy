from DataManager import LocalDataManager

from pithos.tools.lib.client import Pithos_Client, Fault
from dropbox.client import DropboxClient
from dropbox import rest
from oauth2client.client import Credentials
from apiclient.discovery import build
import httplib2


class AuthManager(object):
    def __init__(self):
        self.dataManager = LocalDataManager()

    def pithosAuthentication(self):
        credentials = None
        self.dataManager.update()

        try:
            credentials = self.dataManager.get_pithos_credentials()
        except KeyError:
            return None

        pithosClient = Pithos_Client(credentials['url'], credentials['token'],
                                     credentials['user'])

        try:
            pithosClient.list_containers()
        except Fault:
            return None

        return pithosClient

    def pithosAddUser(self, user, url, token):
        self.dataManager.add_pithos_credentials(user, url, token)
        return self.pithosAuthentication()

    def dropboxAuthentication(self):
        access_token = None
        self.dataManager.update()

        try:
            access_token = self.dataManager.get_dropbox_token()
        except KeyError:
            return None

        dropboxClient = DropboxClient(access_token)
        
        try:
            dropboxClient.account_info()
        except rest.ErrorResponse as e:
            return None
        #RESTSocketError

        return dropboxClient

    def dropboxAddUser(self, key, secret):
        self.dataManager.add_dropbox_token(key,  secret)
        return self.dropboxAuthentication()
    
    #http://tinyurl.com/kdv3ttb
    def googledriveAuthentication(self):
        credentials = None
        self.dataManager.update()

        try:
            credentials = self.dataManager.get_googledrive_credentials()
        except KeyError:
            return None
            
        credentials = Credentials.new_from_json(credentials)
        http = credentials.authorize(httplib2.Http())
        drive_service = build('drive', 'v2', http=http)
        file = drive_service.files().list()
        
        try:
            file.execute()
        except Exception:
            return None
        
        self.dataManager.update_googledrive_credentials(credentials)
        return drive_service
        
    def googledriveAddUser(self, credentials):
        self.dataManager.update_googledrive_credentials(credentials)
        return self.googledriveAuthentication()