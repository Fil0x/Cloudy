class InvalidAuth(Exception):
    '''If the tokens given to a client are invalid.
    '''
    def __init__(self, message):
        Exception.__init__(self, message)
