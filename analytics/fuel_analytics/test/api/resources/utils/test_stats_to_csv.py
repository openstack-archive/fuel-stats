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
import six
import types

from fuel_analytics.test.base import BaseTest
from fuel_analytics.test.base import ElasticTest

from fuel_analytics.api.resources.utils.es_client import EsClient
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv


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

    def test_get_skeleton(self):
        exporter = StatsToCsv()
        data = [
            {'ci': {'p': True, 'e': '@', 'n': 'n'}},
            # reducing fields in nested dict
            {'ci': {'p': False}},
            # adding list values
            {'c': [{'s': 'v', 'n': 2}, {'s': 'vv', 'n': 22}]},
            # adding new value in the list
            {'c': [{'z': 'p'}]},
            # checking empty list
            {'c': []},
            # adding new value
            {'a': 'b'},
        ]
        skeleton = exporter.get_data_skeleton(data)
        self.assertDictEqual(
            {'a': None, 'c': [{'s': None, 'n': None, 'z': None}],
             'ci': {'p': None, 'e': None, 'n': None}},
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

    def test_align_enumerated_field_values(self):
        # Data for checks in format (source, num, expected)
        checks = [
            ([], 0, [False]),
            ([], 1, [False, None]),
            (['a'], 1, [False, 'a']),
            (['a'], 2, [False, 'a', None]),
            (['a', 'b'], 2, [False, 'a', 'b']),
            (['a', 'b'], 1, [True, 'a'])
        ]
        for source, num, expected in checks:
            self.assertListEqual(
                expected,
                StatsToCsv.align_enumerated_field_values(source, num)
            )


class StatsToCsvExportTest(ElasticTest):

    def test_new_param_handled_by_structures_skeleton(self):
        installations_num = 5
        self.generate_data(installations_num=installations_num)

        # Mixing new pram into structures
        es_client = EsClient()
        structures = es_client.get_structures()
        self.assertTrue(isinstance(structures, types.GeneratorType))
        structures = list(structures)
        structures[-1]['mixed_param'] = 'xx'

        exporter = StatsToCsv()
        skeleton = exporter.get_data_skeleton(structures)
        self.assertTrue('mixed_param' in skeleton)

    def test_get_flatten_clusters(self):
        installations_num = 200
        self.generate_data(installations_num=installations_num)
        es_client = EsClient()
        structures = es_client.get_structures()

        exporter = StatsToCsv()
        structure_paths, cluster_paths, csv_paths = \
            exporter.get_cluster_keys_paths()
        flatten_clusters = exporter.get_flatten_clusters(structure_paths,
                                                         cluster_paths,
                                                         structures)
        self.assertTrue(isinstance(flatten_clusters, types.GeneratorType))
        for flatten_cluster in flatten_clusters:
            self.assertEquals(len(csv_paths), len(flatten_cluster))

    def test_flatten_data_as_csv(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)
        es_client = EsClient()
        structures = es_client.get_structures()

        exporter = StatsToCsv()
        structure_paths, cluster_paths, csv_paths = \
            exporter.get_cluster_keys_paths()
        flatten_clusters = exporter.get_flatten_clusters(structure_paths,
                                                         cluster_paths,
                                                         structures)
        self.assertTrue(isinstance(flatten_clusters, types.GeneratorType))
        result = exporter.flatten_data_as_csv(csv_paths, flatten_clusters)
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

    def test_export_clusters(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)

        es_client = EsClient()
        structures = es_client.get_structures()
        exporter = StatsToCsv()
        result = exporter.export_clusters(structures)
        self.assertTrue(isinstance(result, types.GeneratorType))
