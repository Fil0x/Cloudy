import json
import os.path
from configobj import ConfigObj
from Errors import UserNotFound, DuplicateUser, NotInitialized      

#Decorator to check file existence
def checkFile(f):
    def wrapper(*args):
        try:
            with open(args[0].configPath,'r') as file:
                pass
        except IOError:
            args[0]._create_config_file()
        return f(*args)
    return wrapper

class AuthManager(object):
    def __init__(self):
        pass
    
class LocalAuthManager(AuthManager):
    basepath = os.path.join(os.getcwd(), 'Configuration')
    
    def __init__(self, configName='config.ini'):
        self.configPath = os.path.join(self.basepath,configName)
        
        try:
            with open(self.configPath,'r') as f:
                pass
        except IOError as e:
            self._create_config_file()
            
        self.config = ConfigObj(self.configPath)
        
    def _create_config_file(self):
        config = ConfigObj(self.configPath)
        
        config['Application'] = {}
        config['Application']['posX'] = 20
        config['Application']['posY'] = 20
        
        config['Pithos'] = {}
        
        config['Dropbox'] = {}
        config['Dropbox']['APP_KEY'] = '6cmf257smf7esxg'
        config['Dropbox']['APP_SECRET'] = '0eac7yw2tisotrl'
        config['Dropbox']['ACCESS_TYPE'] = 'dropbox'
        
        config['GoogleDrive'] = {}
        config['GoogleDrive']['APP_KEY'] = '638332209096.apps.googleusercontent.com'
        config['GoogleDrive']['APP_SECRET'] = '_8_SU5sLWfoMmS93K--Vg6Ig'
        config['GoogleDrive']['SCOPES'] = 'https://www.googleapis.com/auth/drive'
        config['GoogleDrive']['REDIRECT_URI'] = 'urn:ietf:wg:oauth:2.0:oob'
        
        config['Skydrive'] = {}
        config['Skydrive']['APP_KEY'] = '00000000440D5972'
        config['Skydrive']['APP_SECRET'] = 'wbQU6uGH94Ut18e3AG8iTn0kDwpihAoQ'
        
        config.write()
        
        self.config = ConfigObj(self.configPath)
    
    #Pithos information - Supports multiple users.
    @checkFile
    def get_pithos_user(self, user):
        if user in self.config['Pithos']:
            return self.config['Pithos'][user]
        else:
            raise UserNotFound('{} not found in config file.'.format(user))
    
    @checkFile
    def add_pithos_user(self, user, url, token):
        if user not in self.config['Pithos']:
            self.config['Pithos'][user] = {}
            self.update_pithos_user(user, url, token)
        else:
            raise DuplicateUser('{} already in the config file.'.format(user))
    
    def update_pithos_user(self, user=None, url=None, token=None):
        try:
            self.config['Pithos'][user]['user'] = user or self.config['Pithos'][user]['user']
            self.config['Pithos'][user]['url'] = url or self.config['Pithos'][user]['url']
            self.config['Pithos'][user]['token'] = token or self.config['Pithos'][user]['token']
            
            self.config.write()
        except KeyError:
            raise UserNotFound('{} not found in config file.'.format(user))
    
    #Dropbox information - Supports one user only.
    @checkFile
    def get_dropbox_app_key(self):
        return self.config['Dropbox']['APP_KEY']
        
    @checkFile
    def get_dropbox_app_secret(self):
        return self.config['Dropbox']['APP_SECRET']
        
    @checkFile
    def get_dropbox_access_type(self):
        return self.config['Dropbox']['ACCESS_TYPE']
    
    @checkFile
    def get_dropbox_token(self):
        try:
            return self.config['Dropbox']['access_token']
        except KeyError:
            raise NotInitialized('Access_token is empty')
    
    @checkFile
    def add_dropbox_token(self, key, secret):
        self.config['Dropbox']['access_token'] = {}
        self.update_dropbox_token(key, secret)
    
    def update_dropbox_token(self, key=None, secret=None):
        self.config['Dropbox']['access_token']['key'] = key or self.config['Dropbox']['access_token']['key']
        self.config['Dropbox']['access_token']['secret'] = secret or self.config['Dropbox']['access_token']['secret']
        
        self.config.write()
    
    #Google Drive information - Supports one user only.
    @checkFile
    def get_googledrive_app_key(self):
        return self.config['GoogleDrive']['APP_KEY']
        
    @checkFile
    def get_googledrive_app_secret(self):
        return self.config['GoogleDrive']['APP_SECRET']
        
    @checkFile
    def get_googledrive_scopes(self):
        return self.config['GoogleDrive']['SCOPES']
    
    @checkFile
    def get_googledrive_redirect_uri(self):
        return self.config['GoogleDrive']['REDIRECT_URI']
    
    @checkFile
    def get_googledrive_credentials(self):
        try:
            return self.config['GoogleDrive']['Credentials']
        except KeyError:
            raise NotInitialized('Credentials are empty')
    
    @checkFile
    def update_googledrive_credentials(self, credentials):
        self.config['GoogleDrive']['Credentials'] = credentials.to_json()

        self.config.write()        
    
    #Application information   
    @checkFile
    def get_application_info(self):
        appInfo = self.config['Application']
        for key in appInfo.keys():
            appInfo[key] = int(appInfo[key])
            
        return appInfo
    
    def set_application_info(self, posX=None, posY=None):
        self.config['Application']['posX'] = posX or self.config['Application']['posX']
        self.config['Application']['posY'] = posY or self.config['Application']['posY']
        
        self.config.write()