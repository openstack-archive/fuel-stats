
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

import csv
import io

from analytics.test.base import BaseTest
from analytics.test.base import ElasticTest

from analytics.api.resources.utils.es_client import EsClient
from analytics.api.resources.utils.stats_to_csv import StatsToCsv


class StatsToCsvTest(BaseTest):

    def test_dict_construct_skeleton(self):
        exporter = StatsToCsv()
        data = {'a': 'b'}
        skeleton = exporter.construct_skeleton(data)
        self.assertDictEqual(data, skeleton)

        data = {'a': 'b', 'x': None}
        skeleton = exporter.construct_skeleton(data)
        self.assertDictEqual(data, skeleton)

    def test_list_construct_skeleton(self):
        exporter = StatsToCsv()
        data = ['a', 'b', 'c']
        skeleton = exporter.construct_skeleton(data)
        self.assertListEqual([], skeleton)

        data = [{'a': None}, {'b': 'x'}, {'a': 4, 'c': 'xx'}, {}]
        skeleton = exporter.construct_skeleton(data)
        self.assertListEqual(
            sorted(skeleton[0].keys()),
            sorted(['a', 'b', 'c'])
        )

        data = [
            'a',
            ['a', 'b', []],
            [],
            [{'x': 'z'}, 'zz', {'a': 'b'}],
            ['a'],
            {'p': 'q'}
        ]
        skeleton = exporter.construct_skeleton(data)
        self.assertListEqual([[[], {'a': 'b', 'x': 'z'}], {'p': 'q'}],
                             skeleton)

    def test_get_key_paths(self):
        exporter = StatsToCsv()
        skeleton = {'a': 'b', 'c': 'd'}
        paths = exporter.get_keys_paths(skeleton)
        self.assertListEqual([['a'], ['c']], paths)

        skeleton = {'a': {'e': 'f', 'g': None}}
        paths = exporter.get_keys_paths(skeleton)
        self.assertListEqual([['a', 'e'], ['a', 'g']], paths)

        skeleton = [{'a': 'b', 'c': 'd'}]
        paths = exporter.get_keys_paths(skeleton)
        self.assertListEqual([[]], paths)

    def test_get_flatten_data(self):
        exporter = StatsToCsv()
        data = [
            {'a': 'b', 'c': {'e': 2.1}},
            {'a': 'ee\nxx', 'c': {'e': 3.1415}, 'x': ['z', 'zz']},
        ]
        expected_flatten_data = [
            ['b', 2.1, None],
            ['ee\nxx', 3.1415, 'z zz'],
        ]
        skeleton = exporter.get_data_skeleton(data)
        key_paths = exporter.get_keys_paths(skeleton)

        for idx, expected in enumerate(expected_flatten_data):
            actual = exporter.get_flatten_data(key_paths, data[idx])
            self.assertListEqual(expected, actual)


class StatsToCsvExportTest(ElasticTest):

    def test_new_param_handled_by_structures_skeleton(self):
        installations_num = 5
        self.generate_data(installations_num=installations_num)

        # Mixing new pram into structures
        es_client = EsClient()
        structures = es_client.get_structures()
        structures[-1]['mixed_param'] = 'xx'

        exporter = StatsToCsv()
        skeleton = exporter.get_data_skeleton(structures)
        self.assertTrue('mixed_param' in skeleton)

    def test_get_flatten_clusters(self):
        installations_num = 10
        self.generate_data(installations_num=installations_num)
        es_client = EsClient()
        structures = es_client.get_structures()

        exporter = StatsToCsv()
        clusters_path, flatten_clusters = exporter.get_flatten_clusters(
            structures)
        for flatten_cluster in flatten_clusters:
            self.assertEquals(len(clusters_path), len(flatten_cluster))

    def test_flatten_data_as_csv(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)
        es_client = EsClient()
        structures = es_client.get_structures()

        exporter = StatsToCsv()
        clusters_path, flatten_clusters = exporter.get_flatten_clusters(
            structures)
        output = exporter.flatten_data_as_csv(clusters_path, flatten_clusters)
        output.seek(0, io.SEEK_SET)

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

    def test_export_clusters(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)

        es_client = EsClient()
        structures = es_client.get_structures()
        exporter = StatsToCsv()
        exporter.export_clusters(structures)
