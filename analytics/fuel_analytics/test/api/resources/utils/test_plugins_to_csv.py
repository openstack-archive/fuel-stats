# -*- coding: utf-8 -*-

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
import flask
import mock
import six
import types

from fuel_analytics.test.api.resources.utils.inst_structure_test import \
    InstStructureTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv


class PluginsToCsvExportTest(InstStructureTest, DbTest):

    def test_get_plugin_keys_paths(self):
        exporter = StatsToCsv()
        _, _, _, csv_keys_paths = exporter.get_plugin_keys_paths()
        self.assertTrue(['cluster_id' in csv_keys_paths])
        self.assertTrue(['master_node_uid' in csv_keys_paths])
        self.assertTrue(['name' in csv_keys_paths])
        self.assertTrue(['version' in csv_keys_paths])
        self.assertTrue(['fuel_version' in csv_keys_paths])
        self.assertTrue(['package_version' in csv_keys_paths])

    def test_get_flatten_plugins(self):
        installations_num = 10
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)
        exporter = StatsToCsv()
        structure_paths, cluster_paths, plugins_paths, csv_paths = \
            exporter.get_plugin_keys_paths()
        flatten_plugins = exporter.get_flatten_plugins(
            structure_paths, cluster_paths, plugins_paths, inst_structures)
        self.assertTrue(isinstance(flatten_plugins, types.GeneratorType))
        pos_mn_uid = csv_paths.index(['master_node_uid'])
        pos_cluster_id = csv_paths.index(['cluster_id'])
        for flatten_plugin in flatten_plugins:
            self.assertIsNotNone(flatten_plugin[pos_mn_uid])
            self.assertIsNotNone(flatten_plugin[pos_cluster_id])
            self.assertEquals(len(csv_paths), len(flatten_plugin))

    def test_export_plugins(self):
        installations_num = 100
        exporter = StatsToCsv()
        with app.test_request_context(), mock.patch.object(
                flask.request, 'args', {'from_date': '2015-02-01'}):
            # Creating installation structures
            inst_structures = self.get_saved_inst_structures(
                installations_num=installations_num)
            # Filtering installation structures
            result = exporter.export_plugins(inst_structures)
            self.assertTrue(isinstance(result, types.GeneratorType))
            output = six.StringIO(list(result))
            reader = csv.reader(output)
            for _ in reader:
                pass
