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

from alembic.util import CommandError
from flask import json
import flask_migrate
import os
from unittest2.case import TestCase

from collector.api.app import app
from collector.api.app import db
from collector.api.log import init_logger


flask_migrate.Migrate(app, db)

# Configuring app for the test environment
app.config.from_object('collector.api.config.Testing')
init_logger()


class BaseTest(TestCase):

    def setUp(self):
        self.client = app.test_client()

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data),
                                content_type='application/json')

    def patch(self, url, data):
        return self.client.patch(url, data=json.dumps(data),
                                 content_type='application/json')

    def put(self, url, data):
        return self.client.put(url, data=json.dumps(data),
                               content_type='application/json')

    def get(self, url, data):
        return self.client.get(url, data=json.dumps(data),
                               content_type='application/json')

    def delete(self, url):
        return self.client.delete(url, content_type='application/json')

    def check_response_ok(self, resp, code=200):
        self.assertEquals(code, resp.status_code)
        d = json.loads(resp.data)
        self.assertEquals('ok', d['status'])

    def check_response_error(self, resp, code):
        self.assertEquals(code, resp.status_code)
        d = json.loads(resp.data)
        self.assertEquals('error', d['status'])


class DbTest(BaseTest):

    def setUp(self):
        super(DbTest, self).setUp()

        # Connection must be closed before DB migration
        db.session.close()

        # Cleaning DB. It useful in case of tests failure
        directory = os.path.join(os.path.dirname(__file__),
                                 '..', 'api', 'db', 'migrations')
        with app.app_context():
            try:
                flask_migrate.downgrade(directory=directory)
            except CommandError:
                # Workaround for the first migration
                pass
            flask_migrate.upgrade(directory=directory)
