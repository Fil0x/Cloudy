import os
import logging

import version

#Duplicate logging problem - logging is a singleton.
class LoggerFactory(object):

    def __init__(self):
        print 'init'
        self.v = version.__version__
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        #The application's root logger.
        logger = logging.getLogger(self.v)
        logger.setLevel(logging.DEBUG)

        #Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fmt)

        #Main file handler
        fh = logging.FileHandler(os.path.join('logs', 'main.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)

        #Error file handler
        eh = logging.FileHandler(os.path.join('logs', 'error.log'))
        eh.setLevel(logging.ERROR)
        eh.setFormatter(fmt)

        logger.addHandler(ch)
        logger.addHandler(fh)
        logger.addHandler(eh)

    def getLogger(self, name):
        return logging.getLogger('{}.{}'.format(self.v, name))

def logger_singleton_factory(_singleton=LoggerFactory()):
    return _singleton