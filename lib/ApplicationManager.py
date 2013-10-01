import os
import json

from lib.util import raw
from lib.DataManager import Manager

from configobj import ConfigObj

def check_file(f):
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
        self.config_path = os.path.join(self.basepath, raw(config_path))

        try:
            with open(config_path, 'r') as f:
                pass
        except IOError:
            self._create_config_file()

        self.config = ConfigObj(self.config_path)

    def _create_config_file(self):
        config = ConfigObj(self.config_path)

        config['Detailed'] = {}
        config['Detailed']['pos'] = [-1, -1]
        config['Detailed']['size'] = [-1, -1]
        config['Detailed']['maximized'] = False
        config['Detailed']['screen_id'] = 0

        config['Compact'] = {}
        config['Compact']['pos'] = [-1, -1]
        config['Compact']['screen_id'] = 0

        config['Settings'] = {}

        config['Services'] = []

        config.write()
        
        self.config = ConfigObj(self.config_path)

    def get_services(self):
        return self.config['Services']

    def add_service(self, value):
        assert value not in self.config['Services'], 'Service must be unique'

        self.config['Services'].append(value)

        self.config.write()

    def remove_service(self, value):
        assert value in self.config['Services'], 'Service must be in the list'

        self.config['Services'].remove(value)

        self.config.write()

    def get_pos(self, window):
        ''' window = Detailed, Compact '''
        return self.config[window]['pos']

    def set_pos(self, window, value):
        ''' window = Detailed, Compact , value=List'''
        assert(isinstance(value, list))

        self.config[window]['pos'] = value

        self.config.write()

    def get_size(self):
        return self.config['Detailed']['size']

    def set_size(self, value):
        assert(isinstance(value, list))

        self.config['Detailed']['size'] = value

        self.config.write()

    def get_screen_id(self, window):
        return self.config[window]['screen_id']

    def set_screen_id(self, window, value):
        assert(isinstance(value, int))

        self.config[window]['screen_id'] = value

        self.config.write()

    def get_maximized(self):
        return self.config['Detailed']['maximized']

    def set_maximized(self, value):
        assert(isinstance(value, bool))

        self.config['Detailed']['maximized'] = value

        self.config.write()