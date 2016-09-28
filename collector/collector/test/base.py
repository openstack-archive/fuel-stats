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
app.config.from_envvar('COLLECTOR_SETTINGS', silent=True)
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

    def check_response_ok(self, resp, codes=(200, 201)):
        self.assertIn(resp.status_code, codes)
        d = json.loads(resp.data)
        self.assertEqual('ok', d['status'])

    def check_response_error(self, resp, code):
        self.assertEqual(code, resp.status_code)
        d = json.loads(resp.data)
        self.assertEqual('error', d['status'])


class DbTest(BaseTest):

    def get_migrations_dir(self):
        return os.path.join(os.path.dirname(__file__),
                            '..', 'api', 'db', 'migrations')

    def setUp(self):
        super(DbTest, self).setUp()

        # Cleaning all changes from the previous test
        db.session.rollback()

        directory = self.get_migrations_dir()
        with app.app_context():
            try:
                flask_migrate.downgrade(directory=directory,
                                        revision='base')
            except CommandError as e:
                app.logger.debug("DB migration downgrade failed: %s", e)
                self.clean_db()
            flask_migrate.upgrade(directory=directory)

    def clean_db(self):
        app.logger.debug("Cleaning DB without Alembic")

        # Removing tables
        tables = db.session.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'")
        table_names = list(item[0] for item in tables)
        if table_names:
            app.logger.debug("Removing tables: %s", table_names)
            db.session.execute(
                "DROP TABLE {0} CASCADE".format(','.join(table_names)))

        # Removing sequences
        sequences = list(item[0] for item in db.session.execute(
            "SELECT relname FROM pg_class WHERE relkind='S'"))
        sequence_names = list(item[0] for item in sequences)
        if sequence_names:
            app.logger.debug("Removing sequences: %s", sequence_names)
            db.session.execute(
                "DROP SEQUENCE {0}".format(','.join(sequences)))

        # Removing enums
        enums = db.session.execute(
            "SELECT t.typname FROM pg_type t JOIN pg_catalog.pg_namespace n "
            "ON n.oid = t.typnamespace WHERE n.nspname='public'")
        enum_names = list(item[0] for item in enums)
        if enum_names:
            app.logger.debug("Removing types: %s", enum_names)
            db.session.execute(
                "DROP TYPE {0}".format(','.join(enum_names)))

        # Committing DDL changes
        db.session.commit()
