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


class O(object):
    """Helper object."""
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


class ExportUtilsTest(BaseTest):

    def test_get_key_paths(self):
        skeleton = {'a': 'b', 'c': 'd'}
        paths = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([['a'], ['c']], paths)

        skeleton = {'a': {'e': 'f', 'g': None}}
        paths = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([['a', 'e'], ['a', 'g']], paths)

    def test_get_key_paths_for_lists(self):
        skeleton = {'a': [{'b': None}, 2], 'c': [None, 2]}
        actual = export_utils.get_keys_paths(skeleton)
        expected = [['a', 0, 'b'], ['a', 1, 'b'], ['c', 0], ['c', 1]]
        self.assertListEqual(expected, actual)

        skeleton = {'h': [{'a': 'b', 'c': 'd'}, 1], 't': None}
        actual = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([['h', 0, 'a'], ['h', 0, 'c'], ['t']], actual)

    def test_get_key_paths_for_empty_lists(self):
        skeleton = {'h': [], 't': None}
        actual = export_utils.get_keys_paths(skeleton)
        self.assertListEqual([['h'], ['t']], actual)

    def test_get_flatten_data(self):
        data = [
            {'a': 'b', 'b': {'e': 2.1}},
            {'a': 'ee\nxx', 'b': {'e': 3.1415}, 'c': ['z', 'zz']},
            O('y', {'e': 44}, None),
            O('yy', {'e': 45}, ['b', 'e'])
        ]
        skeleton = {'a': None, 'b': {'e': None}, 'c': [None, 2]}
        expected_flatten_data = [
            ['b', 2.1, None, None],
            ['ee\nxx', 3.1415, 'z', 'zz'],
            ['y', 44, None, None],
            ['yy', 45, 'b', 'e']
        ]

        key_paths = export_utils.get_keys_paths(skeleton)

        for idx, expected in enumerate(expected_flatten_data):
            actual = export_utils.get_flatten_data(key_paths, data[idx])
            self.assertListEqual(expected, actual)

        for idx, data in enumerate(data):
            actual = export_utils.get_flatten_data(key_paths, data)
            self.assertListEqual(expected_flatten_data[idx], actual)

    def test_get_flatten_data_for_functions(self):

        skeleton = {'a': None, 'b': len, 'c': max}
        data = [
            O('y', [1, 2], [0, 42, -1]),
            {'a': 'yy', 'b': {'e': 45}, 'c': ['z', 'e']}
        ]
        expected_flatten_data = [
            ['y', 2, 42],
            ['yy', 1, 'z']
        ]

        key_paths = export_utils.get_keys_paths(skeleton)

        for idx, expected in enumerate(expected_flatten_data):
            actual = export_utils.get_flatten_data(key_paths, data[idx])
            self.assertEqual(expected, actual)

        for idx, data in enumerate(data):
            actual = export_utils.get_flatten_data(key_paths, data)
            self.assertEqual(expected_flatten_data[idx], actual)

    def test_get_flatten_data_for_list(self):
        b_repeats = 1
        e_repeats = 2
        skeleton = {
            'a': None,
            'b': [
                {'d': None, 'e': [{'f': None}, e_repeats]},
                b_repeats
            ],
            'c': []
        }

        expected_keys = [
            ['a'],
            ['b', 0, 'd'], ['b', 0, 'e', 0, 'f'], ['b', 0, 'e', 1, 'f'],
            ['c']
        ]
        self.assertEqual(expected_keys, export_utils.get_keys_paths(skeleton))

        data = [
            O('a_val_o', [{'d': 'd_0_o', 'e': [{'f': 'f_0_o'}]}],
              ['c_o_0', 'c_o_1']),
            {'a': 'a_val', 'b': [{'d': 'd_0', 'e': []}, {'d': 'ignored'}],
             'c': 'c_val'}
        ]

        expected_flatten_data = [
            ['a_val_o', 'd_0_o', 'f_0_o', None, 'c_o_0 c_o_1'],
            ['a_val', 'd_0', None, None, 'c_val'],
        ]

        key_paths = export_utils.get_keys_paths(skeleton)

        for idx, expected in enumerate(expected_flatten_data):
            actual = export_utils.get_flatten_data(key_paths, data[idx])
            self.assertEqual(expected, actual)

        for idx, data in enumerate(data):
            actual = export_utils.get_flatten_data(key_paths, data)
            self.assertEqual(expected_flatten_data[idx], actual)

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
        expected = {'a': None}
        actual = export_utils.construct_skeleton(data)
        self.assertDictEqual(expected, actual)

        data = {'a': 'b', 'x': None}
        expected = {'a': None, 'x': None}
        actual = export_utils.construct_skeleton(data)
        self.assertDictEqual(expected, actual)

    def test_list_construct_skeleton(self):
        data = ['a', 'b', 'c']
        actual = export_utils.construct_skeleton(data)
        self.assertListEqual([], actual)

        data = []
        actual = export_utils.construct_skeleton(data)
        self.assertListEqual([], actual)

        data = [{'a': None}, {'b': 'x'}, {'a': 4, 'c': 'xx'}, {}]
        actual = export_utils.construct_skeleton(data)
        self.assertItemsEqual(
            actual[0].keys(),
            ['a', 'b', 'c']
        )

        data = [
            'a',
            ['a', 'b', []],
            [],
            [{'x': 'z'}, 'zz', {'a': 'b'}],
            ['a'],
            {'p': 'q'}
        ]
        actual = export_utils.construct_skeleton(data)
        expected = [[[], {'a': None, 'x': None}], {'p': None}]
        self.assertListEqual(expected, actual)

    def test_construct_skeleton(self):
        data = {'a': 'b', 'c': [[{'d': 'e'}], 'f']}
        expected = {'a': None, 'c': [[{'d': None}]]}
        actual = export_utils.construct_skeleton(data)
        self.assertEqual(expected, actual)

        data = {'a': {'b': []}}
        expected = {'a': {'b': []}}
        actual = export_utils.construct_skeleton(data)
        self.assertEqual(expected, actual)

        data = {'a': {'b': [{'c': 'd'}, {'e': 'f'}]}}
        expected = {'a': {'b': [{'c': None, 'e': None}]}}
        actual = export_utils.construct_skeleton(data)
        self.assertEqual(expected, actual)

    def test_get_skeleton_for_dicts(self):
        data = [
            {'ci': {'p': True, 'e': '@', 'n': 'n'}},
            # reducing fields in nested dict
            {'ci': {'p': False}},
            # adding new value
            {'a': 'b'},
            # checking empty dict
            {}
        ]
        actual = export_utils.get_data_skeleton(data)
        expected = {'a': None, 'ci': {'p': None, 'e': None, 'n': None}}
        self.assertEqual(expected, actual)

    def test_get_skeleton_for_lists(self):
        data = [
            {'c': [{'s': 'v', 'n': 2}, {'s': 'vv', 'n': 22}]},
            # adding new value in the list
            {'c': [{'z': 'p'}]},
            # checking empty list
            {'c': []},
        ]
        actual = export_utils.get_data_skeleton(data)
        expected = {'c': [{'s': None, 'n': None, 'z': None}]}
        self.assertEqual(expected, actual)

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
        actual = export_utils.get_data_skeleton(data)
        expected = {'a': None, 'ci': {'p': None, 'e': None, 'n': None},
                    'c': [{'s': None, 'n': None, 'z': None}]}
        self.assertEqual(expected, actual)

    def test_get_index(self):

        class Indexed(object):
            """Helper object for testing indexing of objects
            """
            def __init__(self, **kwds):
                self.__dict__.update(kwds)

        checks = [
            (Indexed(**{'one': 1, 'two': 2}), ('one', ), (1,)),
            (Indexed(**{'one': 1, 'two': 2}), ('one', 'two'), (1, 2)),
            (Indexed(**{'one': 1, 'two': 2}), (), ()),
        ]
        for obj, fields, idx in checks:
            self.assertTupleEqual(idx, export_utils.get_index(obj, *fields))
