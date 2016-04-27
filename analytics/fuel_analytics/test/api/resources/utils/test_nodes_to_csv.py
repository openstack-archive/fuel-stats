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
        self.assertTrue(['cluster_id'] in csv_keys_paths)
        self.assertTrue(['cluster_fuel_version'] in csv_keys_paths)
        self.assertTrue(['master_node_uid'] in csv_keys_paths)
        self.assertTrue(['os'] in csv_keys_paths)
        self.assertTrue(['roles', 0] in csv_keys_paths)
        self.assertTrue(['pending_roles', 0] in csv_keys_paths)
        self.assertTrue(['status'] in csv_keys_paths)
        self.assertTrue(['online'] in csv_keys_paths)
        self.assertTrue(['platform_name'] in csv_keys_paths)
        self.assertTrue(['manufacturer'] in csv_keys_paths)
        self.assertTrue(['meta', 'interfaces', 0, 'name'] in csv_keys_paths)
        self.assertTrue(['meta', 'interfaces', 0, 'pxe'] in csv_keys_paths)
        self.assertTrue(['meta', 'interfaces', 0, 'offloading_modes',
                         0, 'state'] in csv_keys_paths)
        self.assertTrue(['meta', 'interfaces', 0, 'interface_properties',
                         'sriov', 'available'] in csv_keys_paths)

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
            self.assertEquals(len(csv_paths), len(flatten_node))

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
