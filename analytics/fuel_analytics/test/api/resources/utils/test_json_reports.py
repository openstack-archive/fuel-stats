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

import json
import memcache
import mock

from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db import model


class JsonReportsTest(DbTest):

    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_get_installations_num(self, _):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={},
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={},
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={},
                is_filtered=True,
                release='8.0'
            ),
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(2, resp['installations']['count'])

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=8.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(1, resp['installations']['count'])

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=xxx'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(0, resp['installations']['count'])

    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_get_env_statuses(self, _):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={
                    'clusters': [
                        {'status': 'new'},
                        {'status': 'operational'},
                        {'status': 'error'}
                    ]
                },
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={
                    'clusters': [
                        {'status': 'deployment'},
                        {'status': 'operational'},
                        {'status': 'operational'},
                    ]
                },
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={
                    'clusters': [
                        {'status': 'deployment'},
                        {'status': 'operational'},
                    ]
                },
                is_filtered=True,
                release='8.0'
            ),
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(
                {'new': 1, 'deployment': 1, 'error': 1, 'operational': 3},
                resp['environments']['statuses']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=8.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(
                {'deployment': 1, 'operational': 2},
                resp['environments']['statuses']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=xxx'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual({}, resp['environments']['statuses'])

    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_get_env_num(self, _):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={'clusters': [{}, {}, {}]},
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={'clusters': [{}, {}]},
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={'clusters': []},
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x3',
                structure={'clusters': []},
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x4',
                structure={'clusters': [{}, {}, {}]},
                is_filtered=True,
                release='8.0'
            ),
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(5, resp['environments']['count'])
            self.assertEqual(
                {'0': 2, '2': 1, '3': 1},
                resp['installations']['environments_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=8.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(2, resp['environments']['count'])
            self.assertEqual(
                {'0': 2, '2': 1},
                resp['installations']['environments_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=xxx'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(0, resp['environments']['count'])
            self.assertEqual({}, resp['installations']['environments_num'])

    @mock.patch.object(memcache.Client, 'set')
    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_caching(self, cached_mc_get, cached_mc_set):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={'clusters': [{}, {}, {}]},
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={'clusters': [{}, {}]},
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={'clusters': [{}]},
                is_filtered=True,
                release='8.0'
            )
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            self.assertEqual(1, cached_mc_get.call_count)
            # Checking that mc.set was called for each release and
            # for all releases summary info
            calls = [
                mock.call(
                    'fuel-stats-installations-infoNone',
                    {'installations': {'environments_num': {2: 1, 3: 1},
                                       'count': 2},
                     'environments': {'count': 5, 'hypervisors_num': {},
                                      'oses_num': {}, 'nodes_num': {},
                                      'operable_envs_count': 0,
                                      'statuses': {}}},
                    3600
                ),
                mock.call(
                    'fuel-stats-installations-info8.0',
                    {'installations': {'environments_num': {2: 1}, 'count': 1},
                     'environments': {'count': 2, 'hypervisors_num': {},
                                      'oses_num': {}, 'nodes_num': {},
                                      'operable_envs_count': 0,
                                      'statuses': {}}},
                    3600
                ),
                mock.call(
                    'fuel-stats-installations-info9.0',
                    {'installations': {'environments_num': {3: 1}, 'count': 1},
                     'environments': {'count': 3, 'hypervisors_num': {},
                                      'oses_num': {}, 'nodes_num': {},
                                      'operable_envs_count': 0,
                                      'statuses': {}}},
                    3600
                ),
            ]
            cached_mc_set.assert_has_calls(calls, any_order=True)
            self.assertEqual(len(calls), cached_mc_set.call_count)

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=8.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            self.assertEqual(2, cached_mc_get.call_count)
            self.assertEqual(len(calls) + 1, cached_mc_set.call_count)
            cached_mc_set.assert_called_with(
                'fuel-stats-installations-info8.0',
                {'installations': {'environments_num': {2: 1}, 'count': 1},
                 'environments': {'count': 2, 'hypervisors_num': {},
                                  'oses_num': {}, 'nodes_num': {},
                                  'operable_envs_count': 0,
                                  'statuses': {}}},
                3600
            )

    @mock.patch.object(memcache.Client, 'set')
    @mock.patch.object(memcache.Client, 'get')
    def test_refresh_cached_data(self, cached_mc_get, cached_mc_set):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={'clusters': [{}, {}, {}]},
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={'clusters': [{}, {}]},
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={'clusters': [{}]},
                is_filtered=True,
                release='8.0'
            )
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations?refresh=1'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            self.assertEqual(0, cached_mc_get.call_count)
            self.assertEquals(3, cached_mc_set.call_count)

    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_get_nodes_num(self, _):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={
                    'clusters': [
                        {'status': 'operational', 'nodes_num': 3},
                        {'status': 'new', 'nodes_num': 2},
                        {'status': 'error', 'nodes_num': 1},
                    ]
                },
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={
                    'clusters': [
                        {'status': 'operational', 'nodes_num': 3}
                    ],
                },
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={
                    'clusters': [
                        {'status': 'operational', 'nodes_num': 5},
                        {'status': 'new', 'nodes_num': 6},
                        {'status': 'error', 'nodes_num': 7},
                    ]
                },
                is_filtered=True,
                release='8.0'
            ),
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(3, resp['environments']['operable_envs_count'])
            self.assertEqual(
                {'3': 2, '1': 1},
                resp['environments']['nodes_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=9.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(2, resp['environments']['operable_envs_count'])
            self.assertEqual(
                {'3': 1, '1': 1},
                resp['environments']['nodes_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=xxx'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(0, resp['environments']['operable_envs_count'])
            self.assertEqual({}, resp['environments']['nodes_num'])

    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_get_hypervisors_num(self, _):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={
                    'clusters': [
                        {'status': 'operational', 'attributes':
                            {'libvirt_type': 'kvm'}},
                        {'status': 'operational', 'attributes':
                            {'libvirt_type': 'Qemu'}},
                        {'status': 'operational', 'attributes':
                            {'libvirt_type': 'Kvm'}},
                        {'status': 'new', 'attributes':
                            {'libvirt_type': 'kvm'}},
                        {'status': 'error', 'attributes':
                            {'libvirt_type': 'qemu'}},
                    ]
                },
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={
                    'clusters': [
                        {'status': 'new', 'attributes':
                            {'libvirt_type': 'qemu'}},
                        {'status': 'error', 'attributes':
                            {'libvirt_type': 'Kvm'}},
                        {'status': 'error', 'attributes':
                            {'libvirt_type': 'vcenter'}},
                    ],
                },
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={
                    'clusters': [
                        {'status': 'operational', 'attributes':
                            {'libvirt_type': 'kvm'}},
                        {'status': 'new', 'attributes':
                            {'libvirt_type': 'kvm'}},
                        {'status': 'error', 'attributes':
                            {'libvirt_type': 'qemu'}},
                    ]
                },
                is_filtered=True,
                release='8.0'
            ),
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(
                {'kvm': 3, 'vcenter': 1, 'qemu': 2},
                resp['environments']['hypervisors_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=8.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(
                {'kvm': 1, 'vcenter': 1},
                resp['environments']['hypervisors_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=xxx'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual({}, resp['environments']['hypervisors_num'])

    @mock.patch.object(memcache.Client, 'get', return_value=None)
    def test_get_oses_num(self, _):
        structures = [
            model.InstallationStructure(
                master_node_uid='x0',
                structure={
                    'clusters': [
                        {'status': 'operational', 'release': {'os': 'Ubuntu'}},
                        {'status': 'error', 'release': {'os': 'ubuntu'}},
                        {'status': 'error', 'release': {'os': 'Centos'}}
                    ]
                },
                is_filtered=False,
                release='9.0'
            ),
            model.InstallationStructure(
                master_node_uid='x1',
                structure={
                    'clusters': [
                        {'status': 'new', 'release': {'os': 'Ubuntu'}},
                        {'status': 'operational', 'release': {'os': 'ubuntu'}}
                    ],
                },
                is_filtered=False,
                release='8.0'
            ),
            model.InstallationStructure(
                master_node_uid='x2',
                structure={
                    'clusters': [
                        {'status': 'new', 'release': {'os': 'centos'}},
                        {'status': 'operational', 'release': {'os': 'centos'}},
                        {'status': 'operational', 'release': {'os': 'centos'}}
                    ]
                },
                is_filtered=True,
                release='8.0'
            ),
        ]
        for structure in structures:
            db.session.add(structure)
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/report/installations'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual(
                {'ubuntu': 3, 'centos': 1},
                resp['environments']['oses_num']
            )

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=8.0'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual({'ubuntu': 1}, resp['environments']['oses_num'])

        with app.test_request_context():
            url = '/api/v1/json/report/installations?release=xxx'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            resp = json.loads(resp.data)
            self.assertEqual({}, resp['environments']['oses_num'])
