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
import os


class Production(object):
    DEBUG = False
    VALIDATE_RESPONSE = False
    LOG_FILE = '/var/log/fuel-stats/collector.log'
    LOG_LEVEL = logging.ERROR
    LOG_ROTATION = False
    LOGGER_NAME = 'collector'
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://collector:*****@localhost/collector'
    # If you need to filter releases please fill FILTERING_RULES
    # Example of FILTERING_RULES:
    # {'6.1':
    #    {
    #        # 6.1 build 2015-04-13_234_13-12-31 became not filtered only
    #        # after 2015-04-30T23:00:18 UTC
    #        '2015-04-13_234_13-12-31': '2015-04-30T23:00:18',
    #
    #        # 6.1 build 2015-04-13_06-18-10 not filtered
    #        '2015-04-13_06-18-10': None
    #  },
    #  '6.1.1': {},  # All builds of 6.1.1 filtered
    #  '7.0': None   # All builds of 7.0 not filtered
    # }
    # If you don't need any filtration, please set FILTERING_RULES = None
    FILTERING_RULES = None


class Testing(Production):
    DEBUG = True
    VALIDATE_RESPONSE = True
    LOG_FILE = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'test', 'logs', 'collector.log'))
    LOG_LEVEL = logging.DEBUG
    LOG_ROTATION = True
    LOG_FILE_SIZE = 2048000
    LOG_FILES_COUNT = 5
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://collector:collector@localhost/collector'
    SQLALCHEMY_ECHO = True
