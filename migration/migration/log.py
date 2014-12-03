#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler

from migration import config


def get_formatter():
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s " \
                 "(%(module)s) %(message)s"
    return Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


def get_file_handler(log_file):
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.LOG_FILE_SIZE,
        backupCount=config.LOG_FILES_COUNT
    )
    formatter = get_formatter()
    file_handler.setFormatter(formatter)
    return file_handler


logger = logging.getLogger('migration')
logger.setLevel(config.LOG_LEVEL)
logger.addHandler(get_file_handler(config.LOG_FILE))

es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(config.LOG_LEVEL)
es_logger.addHandler(get_file_handler(config.LOG_FILE_ES))

est_logger = logging.getLogger('elasticsearch.trace')
est_logger.setLevel(config.LOG_LEVEL)
est_logger.addHandler(get_file_handler(config.LOG_FILE_EST))
