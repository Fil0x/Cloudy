import os

from lib.DataManager import Manager
from lib.DataManager import checkFile

from configobj import ConfigObj

def checkFile(f):
    def wrapper(*args):
        try:
            with open(args[0].config_path,'r') as file:
                pass
        except IOError:
            args[0]._create_config_file()
        return f(*args)
    return wrapper

class ApplicationManager(Manager):
    def __init__(self, config_path='app.ini'):
        self.config_path = os.path.join(self.basepath, config_path)

        try:
            with open(config_path, 'r') as f:
                pass
        except IOError:
            self._create_config_file()

        self.config = ConfigObj(config_path)

    def _create_config_file(self):
        config = ConfigObj(self.config_path)

        config.write()

        self.config = ConfigObj(self.config_path)
