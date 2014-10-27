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

from collector.api.app import db
from collector.api.db.model import InstallationStructure


class TestInstallationStructure(DbTest):

    def test_not_allowed_methods(self):
        resp = self.get('/api/v1/installation_structure/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/installation_structure/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/installation_structure/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/installation_structure/', None)
        self.check_response_error(resp, 405)

    def test_validation_error(self):
        wrong_data_sets = [
            {'installation_structure': {'master_node_uid': 'x'}},
            None,
            {}
        ]
        for data in wrong_data_sets:
            resp = self.post(
                '/api/v1/installation_structure/',
                data
            )
            self.check_response_error(resp, 400)

    def test_post(self):
        master_node_uid = 'x'
        struct = {
            'master_node_uid': master_node_uid,
            'fuel_release': {
                'release': 'r',
                'ostf_sha': 'o_sha',
                'astute_sha': 'a_sha',
                'nailgun_sha': 'n_sha',
                'fuellib_sha': 'fl_sha',
                'feature_groups': ['experimental'],
                'api': 'v1'
            },
            'allocated_nodes_num': 4,
            'unallocated_nodes_num': 4,
            'clusters_num': 2,
            'clusters': [
                {
                    'id': 29,
                    'mode': 'ha_full',
                    'release': {
                        'version': '2014.2-6.0',
                        'name': 'Juno on CentOS 6.5',
                        'os': 'CentOS'
                    },
                    'nodes_num': 3,
                    'nodes': [
                        {'id': 33, 'roles': ['a', 'b', 'c'], 'status': 's'},
                        {'id': 34, 'roles': ['b', 'c'], 'status': 's'},
                        {'id': 35, 'roles': ['c'], 'status': 's'}
                    ]
                },
                {
                    'id': 32,
                    'mode': 'ha_compact',
                    'release': {
                        'version': '2014.2-6.0',
                        'name': 'Juno on CentOS 6.5',
                        'os': 'CentOS'
                    },
                    'nodes_num': 1,
                    'nodes': [
                        {'id': 42, 'roles': ['s'], 'status': 's'}
                    ]
                },
            ]
        }
        resp = self.post(
            '/api/v1/installation_structure/',
            {'installation_structure': struct}
        )
        self.check_response_ok(resp, codes=(201,))
        obj = db.session.query(InstallationStructure).filter(
            InstallationStructure.master_node_uid == master_node_uid).one()
        self.assertDictEqual(struct, obj.structure)
        self.assertIsNotNone(obj.creation_date)
        self.assertIsNone(obj.modification_date)

    def test_post_update(self):
        master_node_uid = 'xx'
        struct = {
            'master_node_uid': master_node_uid,
            'allocated_nodes_num': 0,
            'unallocated_nodes_num': 0,
            'clusters_num': 0,
            'clusters': []
        }
        resp = self.post(
            '/api/v1/installation_structure/',
            {'installation_structure': struct}
        )
        self.check_response_ok(resp, codes=(201,))
        obj_new = db.session.query(InstallationStructure).filter(
            InstallationStructure.master_node_uid == master_node_uid).one()
        self.assertDictEqual(struct, obj_new.structure)
        self.assertIsNotNone(obj_new.creation_date)
        self.assertIsNone(obj_new.modification_date)

        struct['unallocated_nodes_num'] = 5
        resp = self.post(
            '/api/v1/installation_structure/',
            {'installation_structure': struct}
        )
        self.check_response_ok(resp, codes=(200,))
        obj_upd = db.session.query(InstallationStructure).filter(
            InstallationStructure.master_node_uid == master_node_uid).one()
        self.assertDictEqual(struct, obj_upd.structure)
        self.assertIsNotNone(obj_upd.creation_date)
        self.assertIsNotNone(obj_upd.modification_date)
