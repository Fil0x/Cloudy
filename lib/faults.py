class Error(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class InvalidAuth(Error):
    pass
    
class NetworkError(Error):
    pass
