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
from mock import patch

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.common import consts
from collector.api.db.model import ActionLog
from six.moves import xrange


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
        self.check_response_ok(resp)

    def test_post(self):
        master_node_uid = 'x'
        expected_logs = [
            {
                'master_node_uid': master_node_uid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "",
                    "action_name": "",
                    "action_type": "http_request",
                    "start_timestamp": "",
                    "end_timestamp": "",
                    "additional_info": {
                        "request_data": {},
                        "response_data": {}
                    },
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
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        for d in resp_data['action_logs']:
            self.assertEquals(
                consts.ACTION_LOG_STATUSES.added,
                d['status']
            )

        actual_logs = db.session.query(ActionLog).filter(
            ActionLog.master_node_uid == master_node_uid).all()
        self.assertEquals(len(expected_logs), len(actual_logs))
        self.assertListEqual(
            sorted([l['external_id'] for l in expected_logs]),
            sorted([l.external_id for l in actual_logs])
        )

    def test_post_duplication(self):
        master_node_uid = 'x'
        action_logs = [
            {
                'master_node_uid': master_node_uid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "",
                    "action_name": "",
                    "action_type": "nailgun_task",
                    "start_timestamp": "1",
                    "end_timestamp": "2",
                    "additional_info": {
                        "parent_task_id": 0,
                        "subtasks_ids": [],
                        "operation": "",
                        "nodes_from_resp": [],
                        "ended_with_status": ""
                    },
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
        self.check_response_ok(resp)
        count_actual = db.session.query(ActionLog).filter(
            ActionLog.master_node_uid == master_node_uid).count()
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
                'master_node_uid': master_node_uid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "",
                    "action_name": "",
                    "action_type": "nailgun_task",
                    "start_timestamp": "3",
                    "end_timestamp": "4",
                    "additional_info": {
                        "parent_task_id": 0,
                        "subtasks_ids": [],
                        "operation": "",
                        "nodes_from_resp": [],
                        "ended_with_status": ""
                    },
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
        self.check_response_ok(resp)
        count_actual = db.session.query(ActionLog).filter(
            ActionLog.master_node_uid == master_node_uid).count()
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
        expected_logs = [{'master_node_uid': 'x', 'external_id': None}]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': expected_logs}
        )
        self.check_response_error(resp, code=400)

    def test_incomplete_tasks(self):
        master_node_uid = 'x'
        action_logs = [
            {
                'master_node_uid': master_node_uid,
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "cluster_changes",
                    "action_name": "deployment",
                    "action_type": "nailgun_task",
                    "start_timestamp": "1",
                    # about 1/3 is incomplete
                    "end_timestamp": "2" if i % 3 else None,
                    "additional_info": {
                        "parent_task_id": i if i % 2 else None,
                        "subtasks_ids": [],
                        "operation": "deployment"
                    },
                    "is_sent": False,
                    "cluster_id": 5
                }
            }
            for i in xrange(100)]
        completed_count = sum(rec["body"]["end_timestamp"] is not None
                              for rec in action_logs)
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': action_logs}
        )
        self.check_response_ok(resp)

        log_recs = db.session.query(ActionLog).filter(
            ActionLog.master_node_uid == master_node_uid)
        self.assertEqual(
            log_recs.count(),
            completed_count
        )
        for rec in log_recs:
            self.assertIsNotNone(rec.body["end_timestamp"])

        resp_logs = json.loads(resp.data)['action_logs']
        self.assertEqual(
            len(resp_logs),
            len(action_logs)
        )
        passed = sum(r['status'] == consts.ACTION_LOG_STATUSES.added
                     for r in resp_logs)
        skipped = sum(r['status'] == consts.ACTION_LOG_STATUSES.skipped
                      for r in resp_logs)
        self.assertEqual(
            passed + skipped,
            len(action_logs)
        )
        self.assertEqual(
            passed,
            completed_count
        )

    def test_failed_action_logs(self):
        al_num = 100
        action_logs = [
            {
                'master_node_uid': 'xx',
                'external_id': i,
                'body': {
                    "id": i,
                    "actor_id": "",
                    "action_group": "cluster_changes",
                    "action_name": "deployment",
                    "action_type": "nailgun_task",
                    "start_timestamp": "1",
                    "end_timestamp": "2",
                    "additional_info": {
                        "parent_task_id": None,
                        "subtasks_ids": [],
                        "operation": "deployment"
                    },
                    "is_sent": False,
                    "cluster_id": 5
                }
            }
            for i in xrange(al_num)]
        with patch.object(ActionLog.__table__, 'insert',
                          side_effect=Exception('stop')):
            resp = self.post(
                '/api/v1/action_logs/',
                {'action_logs': action_logs}
            )
            self.check_response_ok(resp)

            resp_logs = json.loads(resp.data)['action_logs']
            for r in resp_logs:
                self.assertEqual(consts.ACTION_LOG_STATUSES.failed,
                                 r['status'])

    def test_action_type_action_name_copied_to_columns(self):
        action_logs_data = [
            {
                'master_node_uid': 'xx',
                'external_id': 1,
                'body': {
                    'id': 1,
                    'action_name': 'deployment',
                    'action_type': 'nailgun_task',
                    'end_timestamp': None
                }
            },
            {
                'master_node_uid': 'xx',
                'external_id': 2,
                'body': {
                    'id': 2,
                    'action_name': '',
                    'action_type': 'http_request',
                    'end_timestamp': "1"
                }
            }
        ]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': action_logs_data}
        )
        self.check_response_ok(resp)

        action_logs = db.session.query(ActionLog).all()
        for action_log in action_logs:
            self.assertEqual(action_log.action_name,
                             action_log.body['action_name'])
            self.assertEqual(action_log.action_type,
                             action_log.body['action_type'])
