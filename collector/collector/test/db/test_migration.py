#    Copyright 2016 Mirantis, Inc.
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
import flask_migrate

from collector.test.base import DbTest

from collector.api.app import app
from collector.api.app import db


class TestMigration(DbTest):

    def test_clean_db(self):
        # Crashing alembic versions history
        db.session.execute("UPDATE alembic_version SET version_num='x'")
        db.session.commit()

        migrations_dir = self.get_migrations_dir()
        with app.app_context():
            # Checking migrations are broken
            self.assertRaises(
                CommandError, flask_migrate.downgrade,
                directory=migrations_dir, revision='base'
            )

            self.clean_db()

            # Checking migrations flow is fixed
            flask_migrate.downgrade(directory=migrations_dir, revision='base')
            flask_migrate.upgrade(directory=migrations_dir)
