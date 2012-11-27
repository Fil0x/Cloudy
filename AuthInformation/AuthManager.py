import os.path
from configobj import ConfigObj
from Errors import UserNotFound, DuplicateUser           

#Decorator to check file existence
def checkFile(f):
    def wrapper(*args):
        if not os.path.exists(args[0].configPath):
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
        
        if not os.path.exists(self.configPath):
            self._create_config_file()
        self.config = ConfigObj(self.configPath)
        
    def _create_config_file(self):
        config = ConfigObj(self.configPath)
        
        config['Application'] = {}
        config['Application']['posX'] = 20
        config['Application']['posY'] = 20
        
        config['Pithos'] = {}
        
        config.write()
    
    #Pithos information
    @checkFile
    def get_pithos_info(self, user):
        if user in self.config['Pithos']:
            return self.config['Pithos'][user]
        else:
            raise UserNotFound('{} not found in config file.'.format(user))
    
    @checkFile
    def add_pithos_user(self, user, url, token):
        if user not in self.config['Pithos']:
            self.config['Pithos'][user] = {}
            self.set_pithos_info(user, url, token)
        else:
            raise DuplicateUser('{} already in the config file.'.format(user))
    
    def set_pithos_info(self, user=None, url=None, token=None):
        self.config['Pithos'][user]['user'] = user or self.config['Pithos'][user]['user']
        self.config['Pithos'][user]['url'] = url or self.config['Pithos'][user]['url']
        self.config['Pithos'][user]['token'] = token or self.config['Pithos'][user]['token']
        
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