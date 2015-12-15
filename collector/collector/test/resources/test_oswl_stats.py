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
from collector.api.db.model import OpenStackWorkloadStats as OSWL


class TestOswlStats(DbTest):

    def test_not_allowed_methods(self):
        resp = self.get('/api/v1/oswl_stats/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/oswl_stats/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/oswl_stats/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/oswl_stats/', None)
        self.check_response_error(resp, 405)

    def test_validation_error(self):
        oswls_sets = [
            [{'master_node_uid': 'x', 'cluster_id': None}],
            [{'master_node_uid': 'x', 'cluster_id': 1, 'id': None}]
        ]
        for oswls in oswls_sets:
            resp = self.post(
                '/api/v1/oswl_stats/',
                {'oswl_stats': oswls}
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
                'created_date': datetime.utcnow().date().isoformat(),
                'updated_time': datetime.utcnow().time().isoformat(),
                'resource_data': {
                    'added': [],
                    'current': [],
                    'removed': [],
                    'modified': []
                }
            },
            {
                'master_node_uid': 'x',
                'cluster_id': 1,
                'id': 3,
                'resource_type': consts.OSWL_RESOURCE_TYPES.vm,
                'resource_checksum': 'xx',
                'created_date': datetime.utcnow().date().isoformat(),
                'updated_time': datetime.utcnow().time().isoformat(),
                'resource_data': {
                    'added': [{'id': 1, 'time': 343434343}],
                    'current': [{'id': 'xxx', 'status': 'down'}],
                    'removed': [],
                    'modified': []

                }
            },
            {
                'master_node_uid': 'x',
                'cluster_id': 1,
                'id': 3,
                'resource_type': consts.OSWL_RESOURCE_TYPES.vm,
                'resource_checksum': 'xx',
                'created_date': datetime.utcnow().date().isoformat(),
                'updated_time': datetime.utcnow().time().isoformat(),
                'resource_data': {
                    'added': [{'id': 1, 'time': 343434343}],
                    'current': [{'id': 'xxx', 'status': 'down'}],
                    'removed': [],
                    'modified': []

                },
                'version_info': {
                    'fuel_version': '7.0',
                    'openstack_version': None,
                }
            }
        ]]
        for oswls in oswls_sets:
            resp = self.post(
                '/api/v1/oswl_stats/',
                {'oswl_stats': oswls}
            )
            self.check_response_ok(resp)

    def test_empty_oswl_post(self):
        resp = self.post('/api/v1/oswl_stats/', {'oswl_stats': []})
        self.check_response_ok(resp)

    def generate_dumb_oswls(self, oswls_num):
        return [
            {
                'master_node_uid': 'x',
                'cluster_id': i,
                'id': i,
                'created_date': datetime.utcnow().date().isoformat(),
                'updated_time': datetime.utcnow().time().isoformat(),
                'resource_type': random.choice(consts.OSWL_RESOURCE_TYPES),
                'resource_checksum': 'xx',
                'resource_data': {
                    'added': [],
                    'current': [],
                    'removed': [],
                    'modified': []
                }
            }
            for i in xrange(oswls_num)]

    def generate_oswls_with_version_info(self, oswls_num):
        oswls = self.generate_dumb_oswls(oswls_num)
        version_info_variants = [
            {}, {'fuel_version': None}, {'fuel_version': "7.0"},
            {'release_version': None}, {'release_version': "2015-xx-yy"},
            {'release_os': None}, {'release_os': "OSos"},
            {'release_name': None}, {'release_name': "OSname"},
            {'environment_version': None}, {'environment_version': "OSname"},
            {'fuel_version': 'w', 'release_version': 'x',
             'release_name': 'y', 'release_os': 'z',
             'environment_version': '8.0'}
        ]
        for oswl in oswls:
            oswl['version_info'] = random.choice(version_info_variants)
        return oswls

    def test_existed_oswls_filtering(self):
        oswls_num = 10
        dicts = self.generate_dumb_oswls(oswls_num)
        dict_index_fields = ('master_node_uid', 'id')
        obj_index_fields = ('master_node_uid', 'external_id')
        query = util.get_existed_objects_query(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OSWL
        )

        # We have no objects for update
        self.assertEqual(0, query.count())
        save_oswls = 6
        for d in dicts[:save_oswls]:
            copy_d = d.copy()
            copy_d['external_id'] = copy_d.pop('id')
            db.session.add(OSWL(**copy_d))
        db.session.flush()
        db.session.commit()

        # We have objects for update
        query = util.get_existed_objects_query(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OSWL
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
            OSWL
        )
        util.bulk_insert(dicts_new, OSWL)
        db.session.commit()

    def test_oswls_empty_bulk_insert(self):
        util.bulk_insert([], OSWL)
        db.session.commit()

    def test_oswls_split_new_dicts_and_updated_objs(self):
        oswls_num = 10
        dicts = self.generate_dumb_oswls(oswls_num)
        dict_index_fields = ('master_node_uid', 'id')
        obj_index_fields = ('master_node_uid', 'external_id')
        dicts_new, objs_updated = util.split_new_dicts_and_updated_objs(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OSWL
        )

        # We have no objects for update
        self.assertListEqual([], objs_updated)
        self.assertEqual(oswls_num, len(dicts_new))

        # Saving part of oswls
        oswls_to_save = 3
        util.bulk_insert(dicts_new[:oswls_to_save], OSWL)
        db.session.commit()

        # Adding changes into dicts
        new_cs = 'new_{}'.format(dicts[0]['resource_checksum'])
        dicts[0]['resource_checksum'] = new_cs

        # Checking new dicts and updated objects
        dicts_new, objs_updated = util.split_new_dicts_and_updated_objs(
            dicts,
            zip(dict_index_fields, obj_index_fields),
            OSWL
        )
        self.assertEqual(oswls_num - oswls_to_save, len(dicts_new))
        self.assertEqual(oswls_to_save, len(objs_updated))

        # Checking new checksum value in the updated object
        self.assertEqual(new_cs, objs_updated[0].resource_checksum)

    def test_post(self):
        oswls_num = 20
        expected_oswls = self.generate_dumb_oswls(oswls_num)
        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': expected_oswls}
        )
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        oswls_actual_num = db.session.query(OSWL).count()
        self.assertEqual(oswls_num, oswls_actual_num)
        self.assertEqual(len(resp_data['oswl_stats']), oswls_actual_num)
        for oswl in resp_data['oswl_stats']:
            self.assertEqual(consts.OSWL_STATUSES.added, oswl['status'])

    def test_post_empty(self):
        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': []}
        )
        self.check_response_ok(resp)

    def test_post_duplication(self):
        oswls_num = 30
        expected_oswls = self.generate_dumb_oswls(oswls_num)
        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': expected_oswls}
        )
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        oswls_actual_num = db.session.query(OSWL).count()
        self.assertEqual(oswls_num, oswls_actual_num)
        self.assertEqual(len(resp_data['oswl_stats']), oswls_actual_num)

        # Checking duplication
        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': expected_oswls}
        )
        self.check_response_ok(resp)

    def test_post_updating_objects_ids(self):
        last_oswl = db.session.query(OSWL).order_by(OSWL.id.desc()).first()
        first_ext_id = last_oswl.id + 1 if last_oswl is not None else 2
        oswl_first = {
            'master_node_uid': 'x',
            'cluster_id': 1,
            'id': first_ext_id,
            'created_date': datetime.utcnow().date().isoformat(),
            'updated_time': datetime.utcnow().time().isoformat(),
            'resource_type': consts.OSWL_RESOURCE_TYPES.flavor,
            'resource_checksum': 'xx',
            'resource_data': {
                'added': [],
                'current': [],
                'removed': [],
                'modified': []
            }
        }

        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': [oswl_first]}
        )
        self.check_response_ok(resp)

        first_oswl_db = db.session.query(OSWL).order_by(
            OSWL.id.desc()).first()

        # Set id of the first DB object as external id to the second
        oswl_second = oswl_first.copy()
        oswl_second['id'] = first_oswl_db.id

        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': [oswl_first, oswl_second]}
        )
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        for oswl_stat in resp_data['oswl_stats']:
            self.assertNotEqual(oswl_stat['status'],
                                consts.OSWL_STATUSES.failed)

    def test_post_oswls_with_version_info(self):
        oswls_num = 30
        expected_oswls = self.generate_oswls_with_version_info(oswls_num)
        resp = self.post(
            '/api/v1/oswl_stats/',
            {'oswl_stats': expected_oswls}
        )
        self.check_response_ok(resp)
        resp_data = json.loads(resp.data)
        oswls_actual_num = db.session.query(OSWL).count()
        self.assertEqual(oswls_num, oswls_actual_num)
        self.assertEqual(len(resp_data['oswl_stats']), oswls_actual_num)
