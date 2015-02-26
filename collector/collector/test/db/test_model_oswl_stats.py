#    Copyright 2015 Mirantis, Inc.
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

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.db.model import OpenStackWorkloadStats


class TestModelOswlStatsLog(DbTest):

    def test_unique_constraints(self):
        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid', external_id=1,
            resource_type='vm'))
        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid', external_id=1,
            resource_type='vm'))
        self.assertRaises(IntegrityError, db.session.flush)

    def test_non_nullable_fields(self):
        db.session.add(OpenStackWorkloadStats())
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid'))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid',
            external_id=1))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid',
            external_id=1, cluster_id=2))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid',
            external_id=1, cluster_id=2,
            created_date=datetime.utcnow()))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid',
            external_id=1, cluster_id=2,
            created_date=datetime.utcnow(),
            updated_time=datetime.utcnow().time()))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid',
            external_id=1, cluster_id=2,
            created_date=datetime.utcnow(),
            updated_time=datetime.utcnow().time(),
            resource_checksum=''))
        self.assertRaises(IntegrityError, db.session.flush)
        db.session.rollback()

        # All fields set
        db.session.add(OpenStackWorkloadStats(
            master_node_uid='master_node_uid',
            external_id=1, cluster_id=2,
            created_date=datetime.utcnow(),
            updated_time=datetime.utcnow().time(),
            resource_checksum='', resource_type='vm'))
        db.session.flush()
        db.session.rollback()
