import os.path
from configobj import ConfigObj
from validate import Validator, ValidateError

class AuthManager(object):
    def __init__(self):
        pass
    
class LocalAuthManager(AuthManager):
    basepath = os.getcwd()
    
    def __init__(self, configName='config.ini', validateName='validator.ini'):
        self.configPath = os.path.join(self.basepath,configName)
        self.validatePath = os.path.join(self.basepath,validateName)
        
        if not os.path.exists(self.configPath):
            self._create_config_file()
        if not os.path.exists(self.validatePath):
            self._create_validation_file()
        
        self.config = ConfigObj(self.configPath,configspec=self.validatePath)
        
    def _create_config_file(self):
        config = ConfigObj()
        config.filename = self.configPath
        
        config['Application'] = {}
        config['Application']['windowX'] = 20
        config['Application']['windowY'] = 20
        
        config['Pithos'] = {}
        config['Pithos']['user'] = 'Error'
        config['Pithos']['url'] = 'Error'
        config['Pithos']['token'] = 'Error'
        
        config.write()
    
    def _create_validation_file(self):
        vlt = """
        [Application]
        windowX = integer(default=20)
        windowY = integer(default=20)

        [Pithos]
        user=string(min=6,default='Error')
        url=option('https://pithos.okeanos.grnet.gr/v1','https://pithos.okeanos.io/v1','Error',default='Error')
        token=string(min=15,default='Error')
        """
        
        vlt = '\n'.join([line.strip() for line in vlt.split('\n')])
             
        with open(self.validatePath,'w') as f:
            f.write(vlt)
   
    def _validate_configuration(self):
        '''
        Returns a dictionary with the validation results.
        '''
        validator = Validator()
        return self.config.validate(validator,preserve_errors=True)
        
    #Pithos information
    def get_pithos_user(self):
        return self.config['Pithos']['user']
        
    def get_pithos_url(self):
        return self.config['Pithos']['url']
    
    def get_pithos_token(self):
        return self.config['Pithos']['token']
        
    def set_pithos_user(self,username):
        
    
    #Application information   
    def get_application_info(self):
        appInfo = self.config['Application']
        for key in appInfo.keys():
            appInfo[key] = int(appInfo[key])
            
        return appInfo
    