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
from fuel_analytics.api.resources.utils import export_utils
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv


class StatsToCsvExportTest(InstStructureTest, DbTest):

    def test_get_cluster_keys_paths(self):
        exporter = StatsToCsv()
        _, _, csv_keys_paths = exporter.get_cluster_keys_paths()
        self.assertTrue(['nodes_platform_name_gt3' in csv_keys_paths])
        self.assertTrue(['nodes_platform_name_0' in csv_keys_paths])
        self.assertTrue(['nodes_platform_name_1' in csv_keys_paths])
        self.assertTrue(['nodes_platform_name_2' in csv_keys_paths])
        self.assertTrue(['manufacturer_gt3' in csv_keys_paths])
        self.assertTrue(['manufacturer_0' in csv_keys_paths])
        self.assertTrue(['manufacturer_1' in csv_keys_paths])
        self.assertTrue(['manufacturer_2' in csv_keys_paths])
        self.assertTrue(['attributes', 'heat'] in csv_keys_paths)

    def test_get_flatten_clusters(self):
        installations_num = 200
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)
        exporter = StatsToCsv()
        structure_paths, cluster_paths, csv_paths = \
            exporter.get_cluster_keys_paths()
        flatten_clusters = exporter.get_flatten_clusters(
            structure_paths, cluster_paths, inst_structures)
        self.assertTrue(isinstance(flatten_clusters, types.GeneratorType))
        for flatten_cluster in flatten_clusters:
            self.assertEquals(len(csv_paths), len(flatten_cluster))

    def test_flatten_data_as_csv(self):
        installations_num = 100
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)

        exporter = StatsToCsv()
        structure_paths, cluster_paths, csv_paths = \
            exporter.get_cluster_keys_paths()
        flatten_clusters = exporter.get_flatten_clusters(
            structure_paths, cluster_paths, inst_structures)
        self.assertTrue(isinstance(flatten_clusters, types.GeneratorType))
        result = export_utils.flatten_data_as_csv(csv_paths, flatten_clusters)
        self.assertTrue(isinstance(result, types.GeneratorType))
        output = six.StringIO(list(result))
        reader = csv.reader(output)
        columns = reader.next()

        # Checking enumerated columns are present in the output
        self.assertIn('nodes_manufacturer_0', columns)
        self.assertIn('nodes_manufacturer_gt3', columns)
        self.assertIn('nodes_platform_name_0', columns)
        self.assertIn('nodes_platform_name_gt3', columns)

        # Checking reading result CSV
        for _ in reader:
            pass

    def test_unicode_as_csv(self):
        installations_num = 10
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)

        exporter = StatsToCsv()
        structure_paths, cluster_paths, csv_paths = \
            exporter.get_cluster_keys_paths()
        flatten_clusters = exporter.get_flatten_clusters(
            structure_paths, cluster_paths, inst_structures)
        flatten_clusters = list(flatten_clusters)
        flatten_clusters[1][0] = u'эюя'
        list(export_utils.flatten_data_as_csv(csv_paths, flatten_clusters))

    def test_export_clusters(self):
        installations_num = 100
        inst_structures = self.get_saved_inst_structures(
            installations_num=installations_num)
        exporter = StatsToCsv()
        result = exporter.export_clusters(inst_structures)
        self.assertTrue(isinstance(result, types.GeneratorType))

    def test_filter_by_date(self):
        exporter = StatsToCsv()
        num = 10
        with app.test_request_context():
            inst_structures = self.get_saved_inst_structures(
                installations_num=num)
            with mock.patch.object(flask.request, 'args',
                                   {'from_date': '2015-02-01'}):
                result = exporter.export_clusters(inst_structures)
                self.assertTrue(isinstance(result, types.GeneratorType))
                output = six.StringIO(list(result))
                reader = csv.reader(output)
                for _ in reader:
                    pass
