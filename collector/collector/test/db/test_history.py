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

import copy
import datetime

import json_delta
from sqlalchemy.dialects.postgresql import JSON

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.db import history
from collector.api.db.model import History as H
from collector.api.db.model import HistoryLastSnapshot as HLS


class DbObj(db.Model):
    __tablename__ = 'test_table'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.Integer, nullable=False)
    dt = db.Column(db.DateTime, nullable=False)
    data = db.Column(JSON, nullable=False)


class TestHistory(DbTest):

    def test_history_write_workflow(self):
        external_id = 1
        first_data = {'a': 'a0'}

        obj = DbObj(
            external_id=external_id,
            dt=datetime.datetime.utcnow(),
            data=first_data
        )

        resource_type = DbObj.__tablename__
        resource_ids_names = ('external_id',)
        resource_id = history.get_resource_id(obj, resource_ids_names)

        # The first history write
        history.write_history(obj, resource_ids_names=resource_ids_names)

        last_snapshot = db.session.query(HLS).filter(
            HLS.resource_type == resource_type,
            HLS.resource_id == resource_id).one()
        first_snapshot_date = copy.copy(last_snapshot.created)

        changes = db.session.query(H).filter(
            H.resource_type == resource_type,
            H.resource_id == resource_id).all()
        self.assertEqual([], changes)

        # No history if no changes
        history.write_history(obj, resource_ids_names=resource_ids_names)

        last_snapshot = db.session.query(HLS).filter(
            HLS.resource_type == resource_type,
            HLS.resource_id == resource_id).one()
        self.assertEqual(first_snapshot_date, last_snapshot.created)

        # The second history write
        second_data = {'a': 'a1'}
        obj.data = second_data

        history.write_history(obj, resource_ids_names=resource_ids_names)

        last_snapshot = db.session.query(HLS).filter(
            HLS.resource_type == resource_type,
            HLS.resource_id == resource_id).one()
        second_snapshot_date = copy.copy(last_snapshot.created)

        changes = db.session.query(H).filter(
            H.resource_type == resource_type,
            H.resource_id == resource_id).order_by(H.id.desc()).all()
        self.assertEqual(1, len(changes))

        last_change = changes[0]
        self.assertEqual(first_snapshot_date, last_change.created)

        # The third history write
        second_data = {'a': 'a2'}
        obj.data = second_data

        history.write_history(obj, resource_ids_names=resource_ids_names)

        last_snapshot = db.session.query(HLS).filter(
            HLS.resource_type == resource_type,
            HLS.resource_id == resource_id).one()
        third_snapshot_date = copy.copy(last_snapshot.created)

        changes = db.session.query(H).filter(
            H.resource_type == resource_type,
            H.resource_id == resource_id).order_by(H.id.desc()).all()
        self.assertEqual(2, len(changes))

        last_change = changes[0]
        self.assertEqual(second_snapshot_date, last_change.created)

        # Checking dates in history are growing
        self.assertTrue(first_snapshot_date < second_snapshot_date)
        self.assertTrue(second_snapshot_date < third_snapshot_date)

    def test_data_restoration(self):
        external_id = 1

        data_changes = [
            {'a': 'a0'},
            {'a': 'a1', 'b': 'b0', 'c': [0, 1, 2]},
            {'b': 'b0', 'c': [2, 1]},
            {'c': [2, 1]}
        ]

        obj = DbObj(
            external_id=external_id,
            dt=datetime.datetime.utcnow()
        )
        resource_type = DbObj.__tablename__
        resource_ids_names = ('external_id',)
        resource_id = history.get_resource_id(obj, resource_ids_names)

        for data in data_changes:
            obj.data = data
            history.write_history(obj, resource_ids_names=resource_ids_names)

        last_snapshot = db.session.query(HLS).filter(
            HLS.resource_type == resource_type,
            HLS.resource_id == resource_id).one()

        changes = db.session.query(H).filter(
            H.resource_type == resource_type,
            H.resource_id == resource_id).order_by(H.id.desc()).all()

        data = copy.copy(last_snapshot.data)
        expected_data = list(reversed(data_changes))

        self.assertEqual(expected_data.pop(0), data['data'])

        for idx, change in enumerate(changes):
            data = json_delta.patch(data, change.data_diff, in_place=False)
            obj = DbObj(**data)
            self.assertEqual(expected_data[idx], obj.data)
