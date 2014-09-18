from logging import FileHandler
from logging import Formatter
from logging.handlers import RotatingFileHandler

from collector.api.app import app


def get_file_handler():
    if app.config.get('LOG_ROTATION'):
        file_handler = RotatingFileHandler(app.config.get('LOG_FILE'),
                                           maxBytes=app.config.get('LOG_FILE_SIZE'),
                                           backupCount='LOG_FILES_COUNT')
    else:
        file_handler = FileHandler(app.config.get('LOG_FILE'))
    file_handler.setLevel(app.config.get('LOG_LEVEL'))
    formatter = get_formatter()
    file_handler.setFormatter(formatter)
    return file_handler


def get_formatter():
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s " \
                 "[%(thread)x] (%(module)s) %(message)s"
    return Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


def init_logger():
    app.logger.addHandler(get_file_handler())
