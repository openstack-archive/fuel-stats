from collector.test.base import BaseTest

from collector.api.common.util import build_index
from collector.api.common.util import split_collection


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
            {'id': 1, 'cd': 3, 'msg': 'm'},
            {'id': 2, 'cd': 4, 'msg': 'm'}
        ]

        index = build_index(coll, 'id')
        self.assertEquals(2, len(index))
        self.assertDictEqual(coll[2], index[(1,)])
        self.assertDictEqual(coll[3], index[(2,)])

        index = build_index(coll, 'id', 'cd')
        self.assertEquals(3, len(index))
        self.assertDictEqual(coll[1], index[(1, 2)])
        self.assertDictEqual(coll[2], index[(1, 3)])
        self.assertDictEqual(coll[3], index[(2, 4)])
