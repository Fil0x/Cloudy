import sys
if ".." not in sys.path:
    sys.path.append("..")

from lib.Upload import UploadQueue
from lib.Authentication import AuthManager


#This model is just a container for the required data.
class Model(object):
    def __init__(self):
        #TODO:upload history
        self.uploadQueue = UploadQueue()
        self.authManager = AuthManager()