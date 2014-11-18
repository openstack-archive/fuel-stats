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

import yaml

from flask_migrate import Migrate
from flask_migrate import MigrateCommand
from flask_script import Manager

from collector.api import log
from collector.api.app import app
from collector.api.db.model import *


def external_config_content(conf):
    result = {}
    if conf:
        with open(conf) as f:
            content = yaml.load(f)
            result = content if isinstance(content, dict) else {}
    return result


def configure_app(mode=None, conf=None):
    mode_map = {
        'test': 'collector.api.config.Testing',
        'prod': 'collector.api.config.Production'
    }
    app.config.from_object(mode_map.get(mode))
    app.config.update(**external_config_content(conf))
    log.init_logger()
    return app


manager = Manager(configure_app)
manager.add_option('--mode', help="Acceptable modes. Default: 'test'",
                   choices=('test', 'prod'), default='prod', dest='mode')
manager.add_option('-c', '--config', help="Path to additional yaml config file",
                   dest='conf')

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
