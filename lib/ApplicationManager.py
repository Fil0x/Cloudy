import os
import json

import strings as s
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
        super(ApplicationManager, self).__init__()

        self.config_path = os.path.join(self.basepath, raw(config_path))

        try:
            with open(self.config_path, 'r'):
                pass
        except IOError:
            self._create_config_file()

        self.config = ConfigObj(self.config_path)

    def _create_config_file(self):
        config = ConfigObj(self.config_path)

        config['Detailed'] = {}
        config['Detailed']['pos'] = [30, 30]
        config['Detailed']['size'] = [700, 300]
        config['Detailed']['maximized'] = False
        config['Detailed']['screen_id'] = 0

        config['Compact'] = {}
        config['Compact']['pos'] = [30, 30]
        config['Compact']['screen_id'] = 0
        config['Compact']['orientation'] = 'H' #or 'V'

        config['Settings'] = {}
        config['Settings'][s.popup_checkbox] = False
        config['Settings'][s.alwaysontop_checkbox] = False
        config['Settings'][s.close_checkbox] = False
        config['Settings'][s.stopped_checkbox] = False

        config['Services'] = []

        config.write()

        self.config = ConfigObj(self.config_path)

    def _to_bool(self, attr):
        return self.config['Settings'].as_bool(attr)
        
    def get_general_settings(self):
        self.config['Settings'][s.popup_checkbox] = self._to_bool(s.popup_checkbox)
        self.config['Settings'][s.alwaysontop_checkbox] = self._to_bool(s.alwaysontop_checkbox)
        self.config['Settings'][s.close_checkbox] = self._to_bool(s.close_checkbox)
        self.config['Settings'][s.stopped_checkbox] = self._to_bool(s.stopped_checkbox)

        return self.config['Settings']

    def set_general_settings(self, settings):
        self.config['Settings'] = settings

        self.config.write()

    def get_services(self):
        return self.config.as_list('Services')

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
        pos = map(int, self.config[window]['pos'])
        return pos

    def set_pos(self, window, value):
        ''' window=Detailed,Compact , value=List'''
        assert(isinstance(value, list))

        self.config[window]['pos'] = value

        self.config.write()

    def get_size(self):
        size = map(int, self.config['Detailed']['size'])
        return size

    def set_size(self, value):
        assert(isinstance(value, list))

        self.config['Detailed']['size'] = value

        self.config.write()

    def get_screen_id(self, window):
        return self.config[window]('screen_id')

    def set_screen_id(self, window, value):
        assert(isinstance(value, int))

        self.config[window]['screen_id'] = value

        self.config.write()

    def get_maximized(self):
        return self.config['Detailed'].as_bool('maximized')

    def set_maximized(self, value):
        assert(isinstance(value, bool))

        self.config['Detailed']['maximized'] = value

        self.config.write()

    def get_orientation(self):
        return self.config['Compact']['orientation']

    def set_orientation(self, value):
        assert value in ['V', 'H'], 'Orientation must be V or H'

        self.config['Compact']['orientation'] = value
