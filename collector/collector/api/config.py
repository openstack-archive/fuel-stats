import logging
import os


class Production(object):
    DEBUG = False
    PORT = 5000
    HOST = 'localhost'
    VALIDATE_RESPONSE = False
    LOG_FILE = '/var/log/fuel-stat/collector.log'
    LOG_LEVEL = logging.ERROR
    LOG_ROTATION = False
    LOGGER_NAME = 'collector'
    SQLALCHEMY_DATABASE_URI = 'postgresql://collector:*****@localhost/collector'


class Testing(Production):
    DEBUG = True
    HOST = '0.0.0.0'
    VALIDATE_RESPONSE = True
    LOG_FILE = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'test', 'logs', 'collector.log'))
    LOG_LEVEL = logging.DEBUG
    LOG_ROTATION = True
    LOG_FILE_SIZE = 2048000
    LOG_FILES_COUNT = 5
    SQLALCHEMY_DATABASE_URI = 'postgresql://collector:collector@localhost/collector'
