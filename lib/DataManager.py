import os
import json
import inspect

import local

from configobj import ConfigObj


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

class DataManager(object):
    filedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    basepath =  os.path.join(os.path.dirname(filedir), 'Configuration')

class LocalDataManager(DataManager):
    def __init__(self, configName='config.ini'):
        self.configPath = os.path.join(self.basepath,configName)

        try:
            with open(self.configPath,'r') as f:
                pass
        except IOError as e:
            self._create_config_file()

        self.config = ConfigObj(self.configPath)

    def update(self):
        self.config = ConfigObj(self.configPath)

    def _create_config_file(self):
        config = ConfigObj(self.configPath)

        config['Application'] = {}
        config['Application']['posX'] = 20
        config['Application']['posY'] = 20

        config['Pithos'] = {}
        config['Pithos']['ROOT'] = '/pithos'

        config['Dropbox'] = {}
        config['Dropbox']['APP_KEY'] = local.Dropbox_APPKEY
        config['Dropbox']['APP_SECRET'] = local.Dropbox_APPSECRET
        config['Dropbox']['ROOT'] = '/'

        config['GoogleDrive'] = {}
        config['GoogleDrive']['APP_KEY'] = local.GoogleDrive_APPKEY
        config['GoogleDrive']['APP_SECRET'] = local.GoogleDrive_APPSECRET
        config['GoogleDrive']['SCOPES'] = 'https://www.googleapis.com/auth/drive'
        config['GoogleDrive']['ROOT'] = '/Apps/CSLab_Cloudy'
        config['GoogleDrive']['REDIRECT_URI'] = 'urn:ietf:wg:oauth:2.0:oob'

        config.write()

        self.config = ConfigObj(self.configPath)

    @checkFile
    def get_service_root(self, service):
        return self.config[service]['ROOT']
        
    @checkFile
    def get_pithos_credentials(self):
        try:
            return self.config['Pithos']['credentials']
        except KeyError:
            raise KeyError('Pithos: credentials are empty')

    @checkFile
    def add_pithos_credentials(self, user, url, token):
        self.config['Pithos']['credentials'] = {}
        self.update_pithos_credentials(user, url, token)

    def flush_pithos_credentials(self):
        try:
            del(self.config['Pithos']['credentials'])

            self.config.write()
        except KeyError:
            raise KeyError('Pithos: credentials are empty')

    def update_pithos_credentials(self, user=None, url=None, token=None):
        self.config['Pithos']['credentials']['user'] = user or self.config['Pithos']['credentials']['user']
        self.config['Pithos']['credentials']['url'] = url or self.config['Pithos']['credentials']['url']
        self.config['Pithos']['credentials']['token'] = token or self.config['Pithos']['credentials']['token']

        self.config.write()

    #Dropbox information
    @checkFile
    def get_dropbox_auth_info(self):
        '''Returns the necessary information to request a new dropbox token.
           Order: APP_KEY, APP_SECRET
        '''
        return (self.config['Dropbox']['APP_KEY'],
               self.config['Dropbox']['APP_SECRET'])

    @checkFile
    def get_dropbox_token(self):
        try:
            return self.config['Dropbox']['access_token']
        except KeyError:
            raise KeyError('Dropbox: access_token is empty.')

    @checkFile
    def add_dropbox_token(self, key):
        self.config['Dropbox']['access_token'] = {}
        self.update_dropbox_token(key)

    def flush_dropbox_token(self):
        try:
            del(self.config['Dropbox']['access_token'])

            self.config.write()
        except KeyError:
            raise KeyError('Dropbox: access_token is empty')

    def update_dropbox_token(self, key=None):
        self.config['Dropbox']['access_token'] = key or self.config['Dropbox']['access_token']

        self.config.write()

    #Google Drive information - Supports one user only.
    @checkFile
    def get_googledrive_auth_info(self):
        '''Returns the necessary information to request a new googledrive token.
           Order: APP_KEY, APP_SECRET, SCOPES, REDIRECT_URI
        '''
        return (self.config['GoogleDrive']['APP_KEY'],
               self.config['GoogleDrive']['APP_SECRET'],
               self.config['GoogleDrive']['SCOPES'],
               self.config['GoogleDrive']['REDIRECT_URI'])

    @checkFile
    def set_googledrive_credentials(self, credentials):
        self.config['GoogleDrive']['Credentials'] = credentials.to_json()

        self.config.write()

    @checkFile
    def set_googledrive_root(self, new_root):
        self.config['GoogleDrive']['ROOT'] = new_root

    @checkFile
    def get_googledrive_credentials(self):
        try:
            return self.config['GoogleDrive']['Credentials']
        except KeyError:
            raise KeyError('GoogleDrive: credentials are empty.')

    def flush_googledrive_credentials(self):
        try:
            del(self.config['GoogleDrive']['Credentials'])

            self.config.write()
        except KeyError:
            raise KeyError('GoogleDrive: credentials are empty.')

    #Application information
    @checkFile
    def get_application_info(self):
        appInfo = self.config['Application']
        for key in appInfo.keys():
            appInfo[key] = int(appInfo[key])

        return appInfo

    def update_application_info(self, posX=None, posY=None):
        self.config['Application']['posX'] = posX or self.config['Application']['posX']
        self.config['Application']['posY'] = posY or self.config['Application']['posY']

        self.config.write()