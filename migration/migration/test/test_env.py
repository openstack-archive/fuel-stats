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

from migration import config


def configure_test_env():
    # config parameters substitution for test environment
    config.ELASTIC_HOST = 'localhost'
    config.ELASTIC_PORT = 9200
    config.DB_CONNECTION_STRING = \
        'postgresql://collector:collector@localhost:5432/collector'
    config.LOG_FILE = os.path.realpath(os.path.join(
        os.path.dirname(__file__), 'logs', 'migration.log'))
    config.LOG_LEVEL = logging.DEBUG
