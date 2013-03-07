import sys
if ".." not in sys.path:
    sys.path.append("..")

from lib.Upload import UploadQueue
from lib.Authentication import AuthManager


class Model(object):
    def __init__(self):
        #TODO:upload history
        self.uploadQueue = UploadQueue()
        self.authManager = AuthManager()