from DataManager import LocalDataManager
from Errors import NotInitialized  

from pithos.tools.lib.client import Pithos_Client, Fault
from dropbox import client, rest, session
from oauth2client.client import Credentials
from apiclient.discovery import build
import httplib2
import requests

class AuthManager(object):
    def __init__(self):
        self.dataManager = LocalDataManager()
    
    def pithosAuthentication(self):
        credentials = None
        self.dataManager.update()
        
        try:
            credentials = self.dataManager.get_pithos_credentials()
        except NotInitialized:
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
        except NotInitialized:
            return None
            
        APP_KEY = self.dataManager.get_dropbox_app_key()
        APP_SECRET = self.dataManager.get_dropbox_app_secret()
        ACCESS_TYPE = self.dataManager.get_dropbox_access_type()
        
        sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        sess.set_token(access_token['key'], access_token['secret'])
        dropboxClient = client.DropboxClient(sess)
        
        try:
            dropboxClient.account_info()
        except rest.ErrorResponse as e:
            return None
        #RESTSocketError
        
        return dropboxClient
        
    def dropboxAddUser(self, key, secret):
        self.dataManager.add_dropbox_token(key,  secret)
        return self.dropboxAuthentication()
        
    def googledriveAuthentication(self):
        credentials = None
        self.dataManager.update()
        
        try:
            credentials = self.dataManager.get_googledrive_credentials()
        except NotInitialized:
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
    
    '''
    def skydriveAuthentication(self):
        credentials = None
        self.dataManager.update()
        
        try:
            credentials = self.dataManager.get_skydrive_credentials()
        except NotInitialized:
            return False
            
        resp = requests.get('http://apis.live.net/v5.0/USER_ID?access_token={}'.
                        format(credentials['accesstoken'])
                        
        
        return True
        
    def skydriveAddUser(self, token):
        self.dataManager.update_skydrive_refreshtoken(token)
        return self.skydriveAuthentication()
    '''