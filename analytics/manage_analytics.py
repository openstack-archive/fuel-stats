#!/usr/bin/env python

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

from flask_script import Manager

from analytics.api import log
from analytics.api.app import app


def configure_app(mode=None):
    mode_map = {
        'test': 'analytics.api.config.Testing',
        'prod': 'analytics.api.config.Production'
    }
    app.config.from_object(mode_map.get(mode))
    app.config.from_envvar('ANALYTICS_SETTINGS', silent=True)
    log.init_logger()
    return app


manager = Manager(configure_app)
manager.add_option('--mode', help="Acceptable modes. Default: 'test'",
                   choices=('test', 'prod'), default='prod', dest='mode')


if __name__ == '__main__':
    manager.run()
