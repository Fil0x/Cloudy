import os
import json
import errno
import inspect

import local
import logger
from lib.util import raw

from configobj import ConfigObj


def checkFile(f):
    def wrapper(*args):
        try:
            with open(args[0].configPath,'r') as file:
                pass
        except IOError:
            args[0]._create_config_file()
        return f(*args)
    return wrapper

class Manager(object):
    filedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    basepath =  os.path.join(os.path.dirname(filedir), 'Configuration')
    services = local.services
    
    def __init__(self):   
        try:
            os.makedirs(self.basepath)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

class LocalDataManager(Manager):
    def __init__(self, config_name='config.ini'):
        super(LocalDataManager, self).__init__()
        
        self.configPath = os.path.join(self.basepath,raw(config_name))

        try:
            with open(self.configPath,'r'):
                pass
        except IOError as e:
            self._create_config_file()

        self.config = ConfigObj(self.configPath)

    #Exposed functions
    @checkFile
    def get_service_root(self, service):
        return self.config[service]['ROOT']

    def set_service_root(self, service, root):
        self.config[service]['ROOT'] = root
        self.config.write()
        
    def get_folder_id(self): #GoogleDrive
        return self.config['GoogleDrive']['FOLDER_ID']
        
    def set_folder_id(self, new_id): #GoogleDrive
        self.config['GoogleDrive']['FOLDER_ID'] = new_id
        self.config.write()

    @checkFile
    def get_credentials(self, service):
        try:
            return self.config[service]['credentials']
        except KeyError:
            raise KeyError('{}: credentials are empty'.format(service))

    def set_credentials(self, service, credentials):
        if service == 'Dropbox':
            self.config[service]['credentials'] = credentials[0]
        elif service == 'GoogleDrive':
            self.config[service]['credentials'] = credentials.to_json()
        elif service == 'Pithos':
            self.config[service]['credentials'] = credentials
        self.config.write()

    def flush_credentials(self, service):
        try:
            del(self.config[service]['credentials'])
            self.config.write()
        except KeyError:
            pass
    #End of Exposed functions

    def _create_config_file(self):
        config = ConfigObj(self.configPath)

        config['Pithos'] = {}
        config['Pithos']['ROOT'] = 'Cloudy'

        config['Dropbox'] = {}
        config['Dropbox']['ROOT'] = '/'

        config['GoogleDrive'] = {}
        config['GoogleDrive']['ROOT'] = 'Cloudy'
        config['GoogleDrive']['FOLDER_ID'] = ''

        config.write()

        self.config = ConfigObj(self.configPath)