class UserError(Exception):
    pass
    
class UserNotFound(UserError):
    pass
  
class DuplicateUser(UserError):
    pass
    
class NotInitialized(Exception):
    pass
