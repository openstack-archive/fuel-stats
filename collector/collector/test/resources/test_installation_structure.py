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

import datetime
import mock

from collector.test.base import DbTest

from collector.api.app import app
from collector.api.app import db
from collector.api.db.model import InstallationStructure
from collector.api.resources.installation_structure import _is_filtered


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
                    ],
                    "status": "new",
                    "attributes": {},
                    "network_configuration": {
                        "segmentation_type": "vlan",
                        "net_l23_provider": "ovs"
                    }
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
                    ],
                    "status": "operational",
                    "attributes": {}
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

    def test_valid_fuel_release_content(self):
        master_node_uid = 'x'
        structs = [
            {
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
                'clusters': []
            },
            {
                # In 7.0 ostf_sha renamed, python-fuelclient_sha added
                'master_node_uid': master_node_uid,
                'fuel_release': {
                    'release': 'r',
                    'fuel-ostf_sha': 'f-o_sha',
                    'python-fuelclient_sha': 'p-fc_sha',
                    'astute_sha': 'a_sha',
                    'fuelmain_sha': 'a_sha',
                    'nailgun_sha': 'n_sha',
                    'fuel-library_sha': 'fl_sha',
                    'feature_groups': ['experimental'],
                    'api': 'v1'
                },
                'allocated_nodes_num': 4,
                'unallocated_nodes_num': 4,
                'clusters_num': 2,
                'clusters': []
            },
            {
                # In 8.0 nailgun_sha renamed to fuel-nailgun_sha
                'master_node_uid': master_node_uid,
                'fuel_release': {
                    'release': 'r',
                    'fuel-ostf_sha': 'f-o_sha',
                    'python-fuelclient_sha': 'p-fc_sha',
                    'astute_sha': 'a_sha',
                    'fuelmain_sha': 'a_sha',
                    'fuel-nailgun_sha': 'n_sha',
                    'fuel-library_sha': 'fl_sha',
                    'feature_groups': ['experimental'],
                    'api': 'v1'
                },
                'allocated_nodes_num': 4,
                'unallocated_nodes_num': 4,
                'clusters_num': 2,
                'clusters': []
            },
            {
                # In 8.0 sha checksums removed from the fuel_release
                'master_node_uid': master_node_uid,
                'fuel_release': {
                    'release': 'r',
                    'feature_groups': ['experimental'],
                    'api': 'v1'
                },
                'fuel_packages': [
                    'nailgun-8.0.0-1234'
                ],
                'allocated_nodes_num': 4,
                'unallocated_nodes_num': 4,
                'clusters_num': 2,
                'clusters': []
            },

        ]

        for struct in structs:
            resp = self.post(
                '/api/v1/installation_structure/',
                {'installation_structure': struct}
            )
            self.check_response_ok(resp, codes=(200, 201))

    def test_is_not_filtered(self):
        release = '6.1'
        build_id = '2014-10-30_14-51-06'
        struct = {
            'fuel_release': {
                'release': release,
                'build_id': build_id
            }
        }

        # No rules
        with mock.patch.dict(app.config, {'FILTERING_RULES': None}):
            self.assertFalse(_is_filtered(struct))

        with mock.patch.dict(app.config, {'FILTERING_RULES': {}}):
            self.assertFalse(_is_filtered(struct))

        # No build_ids
        with mock.patch.dict(app.config,
                             {'FILTERING_RULES': {release: None}}):
            self.assertFalse(_is_filtered(struct))

        # Have build id, no from_dt
        with mock.patch.dict(
                app.config, {'FILTERING_RULES': {release: {build_id: None}}}):
            self.assertFalse(_is_filtered(struct))

        # Have build id, from_dt in past
        dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        dt_str = dt.isoformat()
        with mock.patch.dict(
                app.config,
                {'FILTERING_RULES': {release: {build_id: dt_str}}}):
            self.assertFalse(_is_filtered(struct))

    def test_is_filtered(self):
        release = '6.1_filtered'
        build_id = '2014-10-30_14-51-06_filtered'
        struct = {
            'fuel_release': {
                'release': release,
                'build_id': build_id
            }
        }

        # release not found in rules
        with mock.patch.dict(app.config, {'FILTERING_RULES': {'xx': None}}):
            self.assertTrue(_is_filtered(struct))

        # build_id not found in rules
        with mock.patch.dict(app.config,
                             {'FILTERING_RULES': {release: {}}}):
            self.assertTrue(_is_filtered(struct))

        # from_dt in future
        dt = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        dt_str = dt.isoformat()
        with mock.patch.dict(
                app.config,
                {'FILTERING_RULES': {release: {build_id: dt_str}}}):
            self.assertTrue(_is_filtered(struct))

    def test_is_filtered_check_from_dt_formats(self):
        release = 'release_dt_format'
        build_id = 'build_id_dt_format'
        struct = {
            'fuel_release': {
                'release': release,
                'build_id': build_id
            }
        }
        dates = (
            '2015-05-19T11:55:06.369745',
            '2015-05-19T11:55:06',
            '2015-05-19T11:55',
            '2015-05-19T11',
            '2015-05-19T',
            '2015-05-19',
        )
        for from_dt in dates:
            with mock.patch.dict(
                    app.config,
                    {'FILTERING_RULES': {release: {build_id: from_dt}}}):
                _is_filtered(struct)

    def test_not_filtered_saved_in_db(self):
        master_node_uid = 'xx'
        struct = {
            'master_node_uid': master_node_uid,
            'allocated_nodes_num': 0,
            'unallocated_nodes_num': 0,
            'clusters_num': 0,
            'clusters': [],
            'fuel-release': {
                'build_id': 'build_id_not_filtered',
                'release': 'release_not_filtered'
            }
        }
        with mock.patch.dict(app.config, {'FILTERING_RULES': None}):
            resp = self.post(
                '/api/v1/installation_structure/',
                {'installation_structure': struct}
            )
            self.check_response_ok(resp, codes=(201,))

            obj = db.session.query(InstallationStructure).filter(
                InstallationStructure.master_node_uid == master_node_uid).one()
            self.assertFalse(obj.is_filtered)

    def test_filtered_saved_in_db(self):
        master_node_uid = 'xx'
        struct = {
            'master_node_uid': master_node_uid,
            'allocated_nodes_num': 0,
            'unallocated_nodes_num': 0,
            'clusters_num': 0,
            'clusters': [],
            'fuel-release': {
                'build_id': 'build_id_not_filtered',
                'release': 'release_not_filtered'
            }
        }
        with mock.patch.dict(app.config, {'FILTERING_RULES': {'xx': None}}):
            resp = self.post(
                '/api/v1/installation_structure/',
                {'installation_structure': struct}
            )
            self.check_response_ok(resp, codes=(201,))

        obj = db.session.query(InstallationStructure).filter(
            InstallationStructure.master_node_uid == master_node_uid).one()
        self.assertTrue(obj.is_filtered)
