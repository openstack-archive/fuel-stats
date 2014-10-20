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

from flask import json

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.common import consts
from collector.api.db.model import ActionLog


class TestActionLogs(DbTest):

    def test_not_allowed_methods(self):
        resp = self.get('/api/v1/action_logs/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/action_logs/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/action_logs/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/action_logs/', None)
        self.check_response_error(resp, 405)

    def test_empty_action_logs_post(self):
        resp = self.post('/api/v1/action_logs/', {'action_logs': []})
        self.check_response_ok(resp, code=201)

    def test_post(self):
        node_aid = 'x'
        expected_logs = [
            {
                'node_aid': node_aid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "",
                    "action_name": "",
                    "action_type": "",
                    "start_timestamp": "",
                    "end_timestamp": "",
                    "additional_info": {},
                    "is_sent": False,
                    "cluster_id": 5,
                    "task_uuid": None
                }
            }
            for i in xrange(3)]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': expected_logs}
        )
        self.check_response_ok(resp, code=201)
        resp_data = json.loads(resp.data)
        for d in resp_data['action_logs']:
            self.assertEquals(
                consts.ACTION_LOG_STATUSES.added,
                d['status']
            )

        actual_logs = db.session.query(ActionLog).filter(
            ActionLog.node_aid == node_aid).all()
        self.assertEquals(len(expected_logs), len(actual_logs))
        self.assertListEqual(
            sorted([l['external_id'] for l in expected_logs]),
            sorted([l.external_id for l in actual_logs])
        )

    def test_post_duplication(self):
        node_aid = 'x'
        action_logs = [
            {
                'node_aid': node_aid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "",
                    "action_name": "",
                    "action_type": "",
                    "start_timestamp": "",
                    "end_timestamp": "",
                    "additional_info": {},
                    "is_sent": False,
                    "cluster_id": 5,
                    "task_uuid": None
                }
            }
            for i in xrange(100)]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': action_logs}
        )
        self.check_response_ok(resp, code=201)
        count_actual = db.session.query(ActionLog).filter(
            ActionLog.node_aid == node_aid).count()
        resp_data = json.loads(resp.data)
        for d in resp_data['action_logs']:
            self.assertEquals(
                consts.ACTION_LOG_STATUSES.added,
                d['status']
            )
        self.assertEquals(len(action_logs), count_actual)

        # Checking duplications is not added
        new_action_logs = [
            {
                'node_aid': node_aid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "",
                    "action_name": "",
                    "action_type": "",
                    "start_timestamp": "",
                    "end_timestamp": "",
                    "additional_info": {},
                    "is_sent": False,
                    "cluster_id": 5,
                    "task_uuid": None
                }
            }
            for i in xrange(len(action_logs) + 50)]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': action_logs + new_action_logs}
        )
        self.check_response_ok(resp, code=201)
        count_actual = db.session.query(ActionLog).filter(
            ActionLog.node_aid == node_aid).count()
        self.assertEquals(
            len(new_action_logs),
            count_actual
        )
        data = json.loads(resp.data)
        existed = filter(
            lambda x: x['status'] == consts.ACTION_LOG_STATUSES.existed,
            data['action_logs']
        )
        added = filter(
            lambda x: x['status'] == consts.ACTION_LOG_STATUSES.added,
            data['action_logs']
        )
        self.assertEquals(len(action_logs), len(existed))
        self.assertEquals(len(new_action_logs) - len(action_logs), len(added))

    def test_validation_error(self):
        expected_logs = [{'node_aid': 'x', 'external_id': None}]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': expected_logs}
        )
        self.check_response_error(resp, code=400)
