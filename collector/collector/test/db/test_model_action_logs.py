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

from collector.test.base import DbTest

from sqlalchemy.exc import IntegrityError

from collector.api.app import db
from collector.api.db.model import ActionLog


class TestModelActionLog(DbTest):

    def test_unique_constraints(self):
        db.session.add(ActionLog(node_aid='aid', external_id=1))
        db.session.add(ActionLog(node_aid='aid', external_id=1))
        self.assertRaises(IntegrityError, db.session.flush)

    def test_non_nullable_fields(self):
        db.session.add(ActionLog())
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(ActionLog(node_aid='aid'))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()
