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

from fuel_analytics.test.base import BaseTest

from fuel_analytics.api.resources.utils import export_utils


class ExportUtilsTest(BaseTest):

    def test_get_key_paths(self):
        skeleton = {'a': 'b', 'c': 'd'}
        paths = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([['a'], ['c']], paths)

        skeleton = {'a': {'e': 'f', 'g': None}}
        paths = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([['a', 'e'], ['a', 'g']], paths)

        skeleton = [{'a': 'b', 'c': 'd'}]
        paths = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([[]], paths)

    def test_get_flatten_data(self):

        class O(object):
            def __init__(self, a, c, x):
                self.a = a
                self.c = c
                self.x = x

        data = [
            {'a': 'b', 'c': {'e': 2.1}},
            {'a': 'ee\nxx', 'c': {'e': 3.1415}, 'x': ['z', 'zz']},
            O('y', {'e': 44}, None),
            O('yy', {'e': 45}, ['b', 'e'])
        ]
        expected_flatten_data = [
            ['b', 2.1, None],
            ['ee\nxx', 3.1415, 'z zz'],
            ['y', 44, None],
            ['yy', 45, 'b e']
        ]

        skeleton = export_utils.get_data_skeleton(data)
        key_paths = export_utils.get_keys_paths(skeleton)

        for idx, expected in enumerate(expected_flatten_data):
            actual = export_utils.get_flatten_data(key_paths, data[idx])
            self.assertListEqual(expected, actual)

        for idx, data in enumerate(data):
            actual = export_utils.get_flatten_data(key_paths, data)
            self.assertListEqual(expected_flatten_data[idx], actual)

    def test_get_flatten_as_csv_unicode(self):
        data = [
            {'a': u'b'},
            {'a': 'tt', u'эюя': 'x'},
        ]
        expected_csv = [
            'a,эюя\r\n',
            'b,\r\n',
            'tt,x\r\n'
        ]
        skeleton = export_utils.get_data_skeleton(data)
        key_paths = export_utils.get_keys_paths(skeleton)
        flatten_data = []
        for d in data:
            flatten_data.append(export_utils.get_flatten_data(key_paths, d))

        result = export_utils.flatten_data_as_csv(key_paths, flatten_data)
        for idx, actual_csv in enumerate(result):
            self.assertEqual(expected_csv[idx], actual_csv)

    def test_dict_construct_skeleton(self):
        data = {'a': 'b'}
        skeleton = export_utils.construct_skeleton(data)
        self.assertDictEqual(data, skeleton)

        data = {'a': 'b', 'x': None}
        skeleton = export_utils.construct_skeleton(data)
        self.assertDictEqual(data, skeleton)

    def test_list_construct_skeleton(self):
        data = ['a', 'b', 'c']
        skeleton = export_utils.construct_skeleton(data)
        self.assertListEqual([], skeleton)

        data = [{'a': None}, {'b': 'x'}, {'a': 4, 'c': 'xx'}, {}]
        skeleton = export_utils.construct_skeleton(data)
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
        skeleton = export_utils.construct_skeleton(data)
        self.assertListEqual([[[], {'a': 'b', 'x': 'z'}], {'p': 'q'}],
                             skeleton)

    def test_get_skeleton(self):
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
        skeleton = export_utils.get_data_skeleton(data)
        self.assertDictEqual(
            {'a': None, 'c': [{'s': None, 'n': None, 'z': None}],
             'ci': {'p': None, 'e': None, 'n': None}},
            skeleton)

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
                export_utils.align_enumerated_field_values(source, num)
            )
