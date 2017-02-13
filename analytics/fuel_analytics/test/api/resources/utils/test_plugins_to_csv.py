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

import csv
import datetime
import mock
import six
import types

from fuel_analytics.test.api.resources.utils.inst_structure_test import \
    InstStructureTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db import model
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv


class PluginsToCsvExportTest(InstStructureTest, DbTest):

    def test_get_plugin_keys_paths(self):
        exporter = StatsToCsv()
        _, _, _, csv_keys_paths = exporter.get_plugin_keys_paths()
        self.assertTrue(['cluster_id'] in csv_keys_paths)
        self.assertTrue(['cluster_fuel_version'] in csv_keys_paths)
        self.assertTrue(['master_node_uid'] in csv_keys_paths)
        self.assertTrue(['name'] in csv_keys_paths)
        self.assertTrue(['version'] in csv_keys_paths)
        self.assertTrue(['fuel_version'] in csv_keys_paths)
        self.assertTrue(['package_version'] in csv_keys_paths)
        self.assertTrue(['structure', 'fuel_packages'] in csv_keys_paths)

    def test_get_flatten_plugins(self):
        installations_num = 10
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)
        exporter = StatsToCsv()
        structure_paths, cluster_paths, plugins_paths, csv_paths = \
            exporter.get_plugin_keys_paths()
        flatten_plugins = exporter.get_flatten_plugins(
            structure_paths, cluster_paths, plugins_paths, inst_structures)
        self.assertIsInstance(flatten_plugins, types.GeneratorType)
        pos_mn_uid = csv_paths.index(['master_node_uid'])
        pos_cluster_id = csv_paths.index(['cluster_id'])
        for flatten_plugin in flatten_plugins:
            self.assertIsNotNone(flatten_plugin[pos_mn_uid])
            self.assertIsNotNone(flatten_plugin[pos_cluster_id])
            self.assertEqual(len(csv_paths), len(flatten_plugin))

    def test_export_plugins(self):
        installations_num = 100
        exporter = StatsToCsv()
        with app.test_request_context('/?from_date=2015-02-01'):
            # Creating installation structures
            inst_structures = self.get_saved_inst_structures(
                installations_num=installations_num)
            # Filtering installation structures
            result = exporter.export_plugins(inst_structures)
            self.assertIsInstance(result, types.GeneratorType)
            output = six.StringIO(list(result))
            reader = csv.reader(output)
            for _ in reader:
                pass

    def test_plugin_invalid_data(self):
        exporter = StatsToCsv()
        num = 10
        inst_structures = self.get_saved_inst_structures(
            installations_num=num, clusters_num_range=(1, 1),
            plugins_num_range=(1, 1))

        with app.test_request_context():
            # get_flatten_data 3 times called inside get_flatten_plugins
            side_effect = [[]] * num * 3
            side_effect[num / 2] = Exception
            with mock.patch('fuel_analytics.api.resources.utils.'
                            'export_utils.get_flatten_data',
                            side_effect=side_effect):
                structure_paths, cluster_paths, plugins_paths, csv_paths = \
                    exporter.get_plugin_keys_paths()
                flatten_plugins = exporter.get_flatten_plugins(
                    structure_paths, cluster_paths,
                    plugins_paths, inst_structures)
                # Checking only invalid data is not exported
                self.assertEqual(num - 1, len(list(flatten_plugins)))

    def test_fuel_release_info_in_flatten_plugins(self):
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
        structure_paths, cluster_paths, plugins_paths, csv_paths = \
            exporter.get_plugin_keys_paths()
        flatten_plugins = exporter.get_flatten_plugins(
            structure_paths, cluster_paths, plugins_paths, inst_structures)

        pos_fuel_version = csv_paths.index(['cluster_fuel_version'])
        pos_packages = csv_paths.index(['structure', 'fuel_packages'])
        for flatten_plugin in flatten_plugins:
            self.assertEqual(cluster_fuel_version,
                             flatten_plugin[pos_fuel_version])
            self.assertEqual(' '.join(packages),
                             flatten_plugin[pos_packages])
