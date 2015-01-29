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

from datetime import datetime
from flask import json
import random

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.common import consts
from collector.api.common import util
from collector.api.db.model import OpenStackWorkloadStats


class TestOswl(DbTest):

    def test_not_allowed_methods(self):
        resp = self.get('/api/v1/oswl/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/oswl/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/oswl/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/oswl/', None)
        self.check_response_error(resp, 405)

    def test_validation_error(self):
        oswls_sets = [
            [{'master_node_uid': 'x', 'cluster_id': None}],
            [{'master_node_uid': 'x', 'cluster_id': 1, 'id': None}]
        ]
        for oswls in oswls_sets:
            resp = self.post(
                '/api/v1/oswl/',
                {'oswls': oswls}
            )
            self.check_response_error(resp, code=400)

    def test_validation(self):
        oswls_sets = [[
            {
                'master_node_uid': 'x',
                'cluster_id': 1,
                'id': 2,
                'resource_type': consts.OSWL_RESOURCE_TYPES.vm,
                'resource_checksum': 'xx',
                'creation_date': datetime.utcnow().date().isoformat(),
                'update_time': datetime.utcnow().time().isoformat(),
                'resource_data': {
                    'added': {},
                    'current': [],
                    'removed': {},
                    'modified': {}
                }
            },
            {
                'master_node_uid': 'x',
                'cluster_id': 1,
                'id': 3,
                'resource_type': consts.OSWL_RESOURCE_TYPES.vm,
                'resource_checksum': 'xx',
                'creation_date': datetime.utcnow().date().isoformat(),
                'update_time': datetime.utcnow().time().isoformat(),
                'resource_data': {
                    'added': {1: {'time': 343434343}},
                    'current': [{'id': 'xxx', 'status': 'down'}],
                    'removed': {},
                    'modified': {}

                }
            }
        ]]
        for oswls in oswls_sets:
            resp = self.post(
                '/api/v1/oswl/',
                {'oswls': oswls}
            )
            self.check_response_ok(resp)

    def test_empty_oswl_post(self):
        resp = self.post('/api/v1/oswl/', {'oswls': []})
        self.check_response_ok(resp)

    def generate_dumb_oswls(self, oswls_num):
        return [
            {
                'master_node_uid': 'x',
                'cluster_id': i,
                'id': i,
                'creation_date': datetime.utcnow().date().isoformat(),
                'update_time': datetime.utcnow().time().isoformat(),
                'resource_type': random.choice(consts.OSWL_RESOURCE_TYPES),
                'resource_checksum': 'xx',
                'resource_data': {
                    'added': {},
                    'current': [],
                    'removed': {},
                    'modified': {}
                }
            }
            for i in xrange(oswls_num)]

    def test_existed_oswls_filtering(self):
        oswls_num = 10
        dicts = self.generate_dumb_oswls(oswls_num)
        dict_index_fields = ('master_node_uid', 'id')
        obj_index_fields = ('master_node_uid', 'external_id')
        query = util.get_existed_objects_query(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OpenStackWorkloadStats
        )

        # We have no objects for update
        self.assertEqual(0, query.count())
        save_oswls = 6
        for d in dicts[:save_oswls]:
            copy_d = d.copy()
            copy_d['external_id'] = copy_d.pop('id')
            db.session.add(OpenStackWorkloadStats(**copy_d))
        db.session.flush()
        db.session.commit()

        # We have objects for update
        query = util.get_existed_objects_query(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OpenStackWorkloadStats
        )
        self.assertEqual(save_oswls, query.count())

    def test_oswls_bulk_insert(self):
        oswls_num = 10
        dicts = self.generate_dumb_oswls(oswls_num)
        dict_index_fields = ('master_node_uid', 'id')
        obj_index_fields = ('master_node_uid', 'external_id')
        dicts_new, _ = util.split_new_dicts_and_updated_objs(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OpenStackWorkloadStats
        )
        util.bulk_insert(dicts_new, OpenStackWorkloadStats)
        db.session.commit()

    def test_oswls_empty_bulk_insert(self):
        util.bulk_insert([], OpenStackWorkloadStats)
        db.session.commit()

    def test_oswls_split_new_dicts_and_updated_objs(self):
        oswls_num = 10
        dicts = self.generate_dumb_oswls(oswls_num)
        dict_index_fields = ('master_node_uid', 'id')
        obj_index_fields = ('master_node_uid', 'external_id')
        dicts_new, objs_updated = util.split_new_dicts_and_updated_objs(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OpenStackWorkloadStats
        )

        # We have no objects for update
        self.assertListEqual([], objs_updated)
        self.assertEqual(oswls_num, len(dicts_new))

        # Saving part of oswls
        oswls_to_save = 3
        util.bulk_insert(dicts_new[:oswls_to_save], OpenStackWorkloadStats)
        db.session.commit()

        # Adding changes into dicts
        new_cs = 'new_{}'.format(dicts[0]['resource_checksum'])
        dicts[0]['resource_checksum'] = new_cs

        # Checking new dicts and updated objects
        dicts_new, objs_updated = util.split_new_dicts_and_updated_objs(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OpenStackWorkloadStats
        )
        self.assertEqual(oswls_num - oswls_to_save, len(dicts_new))
        self.assertEqual(oswls_to_save, len(objs_updated))

        # Checking new checksum value in the updated object
        self.assertEqual(new_cs, objs_updated[0].resource_checksum)

    def test_post(self):
        oswls_num = 20
        expected_oswls = self.generate_dumb_oswls(oswls_num)
        resp = self.post(
            '/api/v1/oswl/',
            {'oswls': expected_oswls}
        )
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        oswls_actual_num = db.session.query(OpenStackWorkloadStats).count()
        self.assertEqual(oswls_num, oswls_actual_num)
        self.assertEqual(len(resp_data['oswls']), oswls_actual_num)
        for oswl in resp_data['oswls']:
            self.assertEqual(consts.OSWL_STATUSES.added, oswl['status'])

    def test_post_empty(self):
        resp = self.post(
            '/api/v1/oswl/',
            {'oswls': []}
        )
        self.check_response_ok(resp)

    def test_post_duplication(self):
        oswls_num = 30
        expected_oswls = self.generate_dumb_oswls(oswls_num)
        resp = self.post(
            '/api/v1/oswl/',
            {'oswls': expected_oswls}
        )
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        oswls_actual_num = db.session.query(OpenStackWorkloadStats).count()
        self.assertEqual(oswls_num, oswls_actual_num)
        self.assertEqual(len(resp_data['oswls']), oswls_actual_num)

        # Checking duplication
        resp = self.post(
            '/api/v1/oswl/',
            {'oswls': expected_oswls}
        )
        self.check_response_ok(resp)
