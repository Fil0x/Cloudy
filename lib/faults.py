class Error(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

#Global Severity
class NetworkError(Error):
    pass

#Per Service Severity    
class InvalidAuth(Error):
    pass
    
class ServiceUnavailable(Error):
    pass
    
#Per File Severity
class OutOfStorage(Error):
    pass
    
class NonExistentFile(Error):
    pass
