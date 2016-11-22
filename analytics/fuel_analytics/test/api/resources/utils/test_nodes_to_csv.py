# -*- coding: utf-8 -*-

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

import csv
import datetime
import six
import types

from fuel_analytics.test.api.resources.utils.inst_structure_test import \
    InstStructureTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db import model
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv


class NodesToCsvExportTest(InstStructureTest, DbTest):

    def test_get_node_keys_paths(self):
        exporter = StatsToCsv()
        _, _, _, csv_keys_paths = exporter.get_node_keys_paths()
        self.assertNotIn(['manufacturer'], csv_keys_paths)
        self.assertNotIn(['platform_name'], csv_keys_paths)

        self.assertIn(['id'], csv_keys_paths)
        self.assertIn(['group_id'], csv_keys_paths)
        self.assertIn(['cluster_fuel_version'], csv_keys_paths)
        self.assertIn(['master_node_uid'], csv_keys_paths)
        self.assertIn(['os'], csv_keys_paths)
        self.assertIn(['roles', 0], csv_keys_paths)
        self.assertIn(['pending_addition'], csv_keys_paths)
        self.assertIn(['pending_deletion'], csv_keys_paths)
        self.assertIn(['pending_roles', 0], csv_keys_paths)
        self.assertIn(['status'], csv_keys_paths)
        self.assertIn(['online'], csv_keys_paths)

        self.assertIn(['meta', 'cpu', 'real'], csv_keys_paths)
        self.assertIn(['meta', 'cpu', 'total'], csv_keys_paths)
        self.assertIn(['meta', 'cpu', 'spec', 0, 'frequency'], csv_keys_paths)
        self.assertIn(['meta', 'cpu', 'spec', 0, 'model'], csv_keys_paths)

        self.assertIn(['meta', 'memory', 'slots'], csv_keys_paths)
        self.assertIn(['meta', 'memory', 'total'], csv_keys_paths)
        self.assertIn(['meta', 'memory', 'maximum_capacity'], csv_keys_paths)
        self.assertIn(['meta', 'memory', 'devices', 0, 'frequency'],
                      csv_keys_paths)
        self.assertIn(['meta', 'memory', 'devices', 0, 'type'], csv_keys_paths)
        self.assertIn(['meta', 'memory', 'devices', 0, 'size'], csv_keys_paths)

        self.assertIn(['meta', 'disks', 0, 'name'], csv_keys_paths)
        self.assertIn(['meta', 'disks', 0, 'removable'], csv_keys_paths)
        self.assertIn(['meta', 'disks', 0, 'model'], csv_keys_paths)
        self.assertIn(['meta', 'disks', 0, 'size'], csv_keys_paths)

        self.assertIn(['meta', 'system', 'product'], csv_keys_paths)
        self.assertIn(['meta', 'system', 'family'], csv_keys_paths)
        self.assertIn(['meta', 'system', 'version'], csv_keys_paths)
        self.assertIn(['meta', 'system', 'manufacturer'], csv_keys_paths)

        self.assertIn(['meta', 'numa_topology', 'numa_nodes', 0, 'memory'],
                      csv_keys_paths)
        self.assertIn(['meta', 'numa_topology', 'numa_nodes', 0, 'id'],
                      csv_keys_paths)
        self.assertIn(['meta', 'numa_topology', 'supported_hugepages', 0],
                      csv_keys_paths)
        self.assertIn(['meta', 'numa_topology', 'distances', 0],
                      csv_keys_paths)

        self.assertIn(['meta', 'interfaces', 0, 'name'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'pxe'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'driver'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'max_speed'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'offloading_modes',
                       0, 'state'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'offloading_modes',
                       0, 'name'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'offloading_modes', 0, 'sub',
                       0, 'name'], csv_keys_paths)

        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'sriov', 'available'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'sriov', 'enabled'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'sriov', 'physnet'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'sriov', 'sriov_numvfs'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'sriov', 'sriov_totalvfs'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'dpdk', 'enabled'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'mtu'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'disable_offloading'], csv_keys_paths)
        self.assertIn(['meta', 'interfaces', 0, 'interface_properties',
                       'numa_node'], csv_keys_paths)

    def test_get_flatten_nodes(self):
        installations_num = 10
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)
        exporter = StatsToCsv()
        structure_paths, cluster_paths, node_paths, csv_paths = \
            exporter.get_node_keys_paths()
        flatten_nodes = exporter.get_flatten_nodes(
            structure_paths, cluster_paths, node_paths, inst_structures)
        self.assertTrue(isinstance(flatten_nodes, types.GeneratorType))
        pos_mn_uid = csv_paths.index(['master_node_uid'])
        pos_cluster_id = csv_paths.index(['cluster_id'])
        pos_status = csv_paths.index(['status'])
        for flatten_node in flatten_nodes:
            self.assertIsNotNone(flatten_node[pos_mn_uid])
            self.assertIsNotNone(flatten_node[pos_cluster_id])
            self.assertIsNotNone(flatten_node[pos_status])
            self.assertEqual(len(csv_paths), len(flatten_node))

    def test_export_nodes(self):
        installations_num = 100
        exporter = StatsToCsv()
        with app.test_request_context('/?from_date=2015-02-01'):
            # Creating installation structures
            inst_structures = self.get_saved_inst_structures(
                installations_num=installations_num)
            # Filtering installation structures
            result = exporter.export_nodes(inst_structures)
            self.assertTrue(isinstance(result, types.GeneratorType))
            output = six.StringIO(list(result))
            reader = csv.reader(output)
            for _ in reader:
                pass

    def test_fuel_release_info_in_flatten_nodes(self):
        inst_fuel_version = '8.0'
        cluster_fuel_version = '7.0'
        packages = ['z', 'a', 'c']
        inst_structures = [
            model.InstallationStructure(
                master_node_uid='one',
                creation_date=datetime.datetime.utcnow(),
                is_filtered=False,
                structure={
                    'fuel_release': {'release': inst_fuel_version},
                    'fuel_packages': packages,
                    'clusters': [{
                        'id': 1, 'nodes': [],
                        'fuel_version': cluster_fuel_version,
                        'installed_plugins': [{
                            'name': 'plugin_a',
                            'version': 'plugin_version_0',
                            'releases': [],
                            'fuel_version': ['8.0', '7.0'],
                            'package_version': 'package_version_0'
                        }],
                    }]
                }
            )
        ]
        for structure in inst_structures:
            db.session.add(structure)
        db.session.flush()

        exporter = StatsToCsv()
        structure_paths, cluster_paths, node_paths, csv_paths = \
            exporter.get_node_keys_paths()
        flatten_nodes = exporter.get_flatten_nodes(
            structure_paths, cluster_paths, node_paths, inst_structures)

        pos_fuel_version = csv_paths.index(['cluster_fuel_version'])
        pos_packages = csv_paths.index(['structure', 'fuel_packages'])
        for flatten_node in flatten_nodes:
            self.assertEqual(cluster_fuel_version,
                             flatten_node[pos_fuel_version])
            self.assertEqual(' '.join(packages),
                             flatten_node[pos_packages])
