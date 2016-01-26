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
from collector.api.config import index_filtering_rules
from collector.api.db.model import InstallationStructure
from collector.api.resources.installation_structure import _is_filtered
from collector.api.resources.installation_structure import \
    _is_filtered_by_build_info


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

    def test_is_not_filtered_by_build_id(self):
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

    def test_is_not_filtered_by_packages(self):
        release = '8.0'
        packages = ['z_filtered', 'a_filtered']
        sorted_packages = tuple(sorted(packages))
        struct = {
            'fuel_release': {
                'release': release
            },
            'fuel_packages': packages
        }

        # Have 'packages', no from_dt
        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: {sorted_packages: None}}}
        ):
            self.assertFalse(_is_filtered(struct))

        # Have 'packages', from_dt in past
        dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        dt_str = dt.isoformat()
        with mock.patch.dict(
                app.config,
                {'FILTERING_RULES': {release: {sorted_packages: dt_str}}}):
            self.assertFalse(_is_filtered(struct))

    def test_is_not_filtered_by_packages_and_build_id(self):
        release = '8.0'
        packages = ['z_filtered', 'a_filtered']
        sorted_packages = tuple(sorted(packages))
        build_id = '2016-01-26'
        struct = {
            'fuel_release': {
                'release': release,
                'build_id': build_id
            },
            'fuel_packages': packages
        }

        # No rules
        with mock.patch.dict(app.config, {'FILTERING_RULES': None}):
            self.assertFalse(_is_filtered(struct))

        with mock.patch.dict(app.config, {'FILTERING_RULES': {}}):
            self.assertFalse(_is_filtered(struct))

        # No build info
        with mock.patch.dict(app.config,
                             {'FILTERING_RULES': {release: None}}):
            self.assertFalse(_is_filtered(struct))

        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: {sorted_packages: None,
                                           build_id: None}}}
        ):
            self.assertFalse(_is_filtered(struct))

        # Have build info, from_dt in past
        dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        dt_str = dt.isoformat()

        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: {sorted_packages: dt_str,
                                           build_id: dt_str}}}
        ):
            self.assertFalse(_is_filtered(struct))

    def test_is_filtered_by_packages_and_build_id(self):
        release = '8.0_filtered'
        packages = ['z_filtered', 'a_filtered']
        build_id = '2016-01-26_filtered'
        sorted_packages = tuple(sorted(packages))
        struct = {
            'fuel_release': {
                'release': release,
                'build_id': build_id
            },
            'fuel_packages': packages
        }

        # build_info not found in rules
        with mock.patch.dict(app.config, {'FILTERING_RULES': {'xx': None}}):
            self.assertTrue(_is_filtered(struct))

        # build_info not found in rules
        with mock.patch.dict(app.config,
                             {'FILTERING_RULES': {release: {}}}):
            self.assertTrue(_is_filtered(struct))

        # from_dt in future
        dt = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        dt_str = dt.isoformat()
        with mock.patch.dict(
                app.config,
                {'FILTERING_RULES': {release: {sorted_packages: dt_str}}}):
            self.assertTrue(_is_filtered(struct))

        with mock.patch.dict(
                app.config,
                {'FILTERING_RULES': {release: {build_id: dt_str}}}):
            self.assertTrue(_is_filtered(struct))

        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: {sorted_packages: dt_str,
                                           build_id: dt_str}}}
        ):
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

    def test_is_filtered_by_build_info_by_build_id(self):
        build_id = 'build_01'

        # Checking 'build_id' not in filtering rules
        filtering_rules = {}
        self.assertTrue(_is_filtered_by_build_info(build_id, filtering_rules))

        # Checking filtering by time
        from_dt = datetime.datetime.utcnow() + datetime.timedelta(days=2)
        from_dt_str = from_dt.isoformat()
        filtering_rules = {build_id: from_dt_str}
        self.assertTrue(_is_filtered_by_build_info(build_id, filtering_rules))

    def test_is_not_filtered_by_build_info_by_build_id(self):
        # Checking not filtered if 'build_id' not defined
        self.assertFalse(_is_filtered_by_build_info(None, {}))

        # Checking filtering by time
        build_id = 'build_02'
        from_dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        from_dt_str = from_dt.isoformat()
        filtering_rules = {build_id: from_dt_str}
        self.assertFalse(_is_filtered_by_build_info(build_id, filtering_rules))

    def test_is_filtered_by_build_info_by_packages(self):
        packages = ('z', 'a', 'b')

        # Checking 'packages' not in filtering rules
        filtering_rules = {}
        self.assertTrue(_is_filtered_by_build_info(packages, filtering_rules))

        # Checking 'packages' doesn't match
        filtering_rules = {packages[:-1]: None}
        self.assertTrue(_is_filtered_by_build_info(packages, filtering_rules))

        filtering_rules = {tuple(sorted(packages))[:-1]: None}
        self.assertTrue(_is_filtered_by_build_info(packages, filtering_rules))

        # Checking not sorted 'packages' is filtered
        filtering_rules = {packages: None}
        self.assertTrue(_is_filtered_by_build_info(packages, filtering_rules))

        # Checking filtering by time
        from_dt = datetime.datetime.utcnow() + datetime.timedelta(days=2)
        from_dt_str = from_dt.isoformat()
        filtering_rules = {packages: from_dt_str}
        self.assertTrue(_is_filtered_by_build_info(packages, filtering_rules))

    def test_is_not_filtered_by_build_info_by_packages(self):
        # Checking not filtered if 'packages' not defined
        self.assertFalse(_is_filtered_by_build_info(None, {}))

        # Checking filtering by time
        packages = ('z', 'a', 'b')
        from_dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        from_dt_str = from_dt.isoformat()
        filtering_rules = {tuple(sorted(packages)): from_dt_str}
        self.assertFalse(_is_filtered_by_build_info(packages, filtering_rules))

    def test_filtering_rules_indexed(self):
        build_id = 'build_id_0'
        filtering_rules = {(3, 2, 1): None, (2, 1): '2016-01-26',
                           'build_id': build_id}
        release = '8.0'
        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: filtering_rules.copy()}}
        ):
            # Checking filtering rules before sorting
            actual_filtering_rules = app.config.get('FILTERING_RULES')[release]
            for packages, from_dt in filtering_rules.iteritems():
                if isinstance(packages, tuple):
                    self.assertNotIn(tuple(sorted(packages)),
                                     actual_filtering_rules)
                    self.assertIn(packages, actual_filtering_rules)

            # Checking filtering rules after sorting
            index_filtering_rules(app)
            actual_filtering_rules = app.config.get('FILTERING_RULES')[release]
            for packages, from_dt in filtering_rules.iteritems():
                if isinstance(packages, tuple):
                    self.assertIn(tuple(sorted(packages)),
                                  actual_filtering_rules)
                    self.assertNotIn(packages, actual_filtering_rules)
            self.assertEqual(build_id, actual_filtering_rules['build_id'])
