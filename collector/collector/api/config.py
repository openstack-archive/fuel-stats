class Production(object):
    DEBUG = False
    PORT = 5000
    HOST = 'localhost'
    VALIDATE_RESPONSE = False


class Testing(Production):
    DEBUG = True
    HOST = '0.0.0.0'
    VALIDATE_RESPONSE = True
