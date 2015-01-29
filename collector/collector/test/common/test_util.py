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

from collector.test.base import BaseTest

from collector.api.common.util import build_index
from collector.api.common.util import get_index
from collector.api.common.util import split_collection


class Indexed(object):
    """Helper object for testing indexing of objects
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class TestUtil(BaseTest):

    def test_split_collection(self):
        coll = list(xrange(3))
        chunks = list(split_collection(coll, chunk_size=len(coll)))
        self.assertEquals(1, len(chunks))
        self.assertListEqual(chunks[0], coll)

        chunks = list(split_collection(coll, chunk_size=len(coll) + 1))
        self.assertEquals(1, len(chunks))
        self.assertListEqual(chunks[0], coll)

        chunks = list(split_collection(coll, chunk_size=len(coll) - 1))
        self.assertEquals(2, len(chunks))
        self.assertListEqual(chunks[0], coll[:-1])
        self.assertListEqual(chunks[1], coll[-1:])

    def test_build_index(self):
        coll = [
            {'id': 1, 'cd': 2, 'msg': 'm'},
            {'id': 1, 'cd': 2, 'msg': 'm'},
            Indexed(**{'id': 1, 'cd': 3, 'msg': 'm'}),
            Indexed(**{'id': 2, 'cd': 4, 'msg': 'm'})
        ]

        index = build_index(coll, 'id')
        self.assertEqual(2, len(index))
        self.assertEqual(coll[2], index[(1,)])
        self.assertEqual(coll[3], index[(2,)])

        index = build_index(coll, 'id', 'cd')
        self.assertEqual(3, len(index))
        self.assertDictEqual(coll[1], index[(1, 2)])
        self.assertEqual(coll[2], index[(1, 3)])
        self.assertEqual(coll[3], index[(2, 4)])

    def test_get_index(self):
        checks = [
            (Indexed(**{'one': 1, 'two': 2}), ('one', ), (1,)),
            (Indexed(**{'one': 1, 'two': 2}), ('one', 'two'), (1, 2)),
            (Indexed(**{'one': 1, 'two': 2}), (), ()),
        ]
        for obj, fields, idx in checks:
            self.assertTupleEqual(
                idx,
                get_index(obj, *fields)
            )
