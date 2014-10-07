from collections import namedtuple
from datetime import datetime
from analytics.test.base import ElasticTest


class NodesDistribution(ElasticTest):

    def setUp(self):
        super(NodesDistribution, self).setUp()
        # cleaning index
        self.es.indices.delete(self.INDEX_FUEL, ignore=[404])
        self.es.indices.create(self.INDEX_FUEL)

    def test_report(self):
        docs = [
            {
                'aid': 'x0',
                'on_date': datetime.now(),
                'clusters_num': 1,
                'allocated_nodes_num': 1,
                'unallocated_nodes_num': 4,
                'clusters': [
                    {'id': 1,
                     'nodes_num': 1,
                     'nodes': [
                         {'id': 2, 'roles': ['a', 'b']}
                     ]}
                ]
            },
            {
                'aid': 'x1',
                'on_date': datetime(2014, 01, 01, hour=12, minute=34),
                'clusters_num': 2,
                'allocated_nodes_num': 7,
                'unallocated_nodes_num': 0,
                'clusters': [
                    {'id': 1,
                     'nodes_num': 5,
                     'nodes': [
                         {'id': 1, 'roles': []},
                         {'id': 10, 'roles': ['a', 'c']},
                         {'id': 15, 'roles': ['a', 'c']},
                         {'id': 16, 'roles': ['a', 'c']},
                         {'id': 17, 'roles': ['a', 'd']}
                     ]},
                    {'id': 3,
                     'nodes_num': 2,
                     'nodes': [
                         {'id': 1, 'roles': ['e']},
                         {'id': 10, 'roles': ['a', 'c', 'd']}
                     ]},
                ]
            },
            {
                'aid': 'x11',
                'on_date': datetime.now(),
                'clusters_num': 1,
                'allocated_nodes_num': 7,
                'unallocated_nodes_num': 0,
                'clusters': [
                    {'id': 1,
                     'nodes_num': 7,
                     'nodes': [
                         {'id': 1, 'roles': []},
                         {'id': 10, 'roles': ['a', 'c']},
                         {'id': 15, 'roles': ['a', 'c']},
                         {'id': 16, 'roles': ['a', 'c']},
                         {'id': 17, 'roles': ['a', 'd']},
                         {'id': 21, 'roles': ['e']},
                         {'id': 22, 'roles': ['a', 'c', 'd']}
                     ]}
                ]
            },
            {
                'aid': 'x12',
                'on_date': datetime.now(),
                'clusters_num': 1,
                'allocated_nodes_num': 5,
                'unallocated_nodes_num': 0,
                'clusters': [
                    {'id': 1,
                     'nodes_num': 5,
                     'nodes': [
                         {'id': 1, 'roles': []},
                         {'id': 10, 'roles': ['a', 'c']},
                         {'id': 15, 'roles': ['a', 'c']},
                         {'id': 16, 'roles': ['a', 'c']},
                         {'id': 17, 'roles': ['a', 'd']},
                     ]}
                ]
            },
            {
                'aid': 'x2',
                'on_date': datetime.now(),
                'clusters_num': 2,
                'allocated_nodes_num': 13,
                'unallocated_nodes_num': 10,
                'clusters': [
                    {'id': 100,
                     'nodes_num': 9,
                     'nodes': [
                         {'id': 1, 'roles': []},
                         {'id': 2, 'roles': []},
                         {'id': 3, 'roles': []},
                         {'id': 4, 'roles': []},
                         {'id': 5, 'roles': []},
                         {'id': 6, 'roles': ['a']},
                         {'id': 7, 'roles': ['a']},
                         {'id': 8, 'roles': ['a']},
                         {'id': 9, 'roles': ['a']},
                     ]},
                    {'id': 300,
                     'nodes_num': 4,
                     'nodes': [
                         {'id': 10, 'roles': ['e']},
                         {'id': 11, 'roles': ['a', 'c', 'd']},
                         {'id': 12, 'roles': ['a', 'c', 'd']},
                         {'id': 13, 'roles': ['a', 'c', 'd']},
                     ]},
                ]
            },
            {
                'aid': 'x4',
                'on_date': datetime.now(),
                'clusters_num': 0,
                'allocated_nodes_num': 0,
                'unallocated_nodes_num': 0,
                'clusters': []
            },
            {
                'aid': 'x5',
                'on_date': datetime.now(),
                'clusters_num': 1,
                'allocated_nodes_num': 0,
                'unallocated_nodes_num': 2,
                'clusters': [
                    {'id': 1, 'nodes_num': 0, 'nodes': []}
                ]
            },
        ]

        for doc in docs:
            self.es.index(self.INDEX_FUEL, self.DOC_TYPE_INSTALLATION, doc, id=doc['aid'])

        self.es.indices.refresh(self.INDEX_FUEL)

        # nodes distribution request
        nodes_distribution = {
            "size": 0,
            "aggs": {
                "nodes_distribution": {
                    "histogram": {
                        "field": "allocated_nodes_num",
                        "interval": 1
                    }
                }
            }
        }

        resp = self.es.search(index='fuel', doc_type='installation', body=nodes_distribution)
        result = resp['aggregations']['nodes_distribution']['buckets']
        self.assertGreaterEqual(len(docs), len(result))
        AggsCheck = namedtuple('AggsCheck', ['key', 'doc_count'])
        checks = (
            AggsCheck(0, 2),
            AggsCheck(1, 1),
            AggsCheck(5, 1),
            AggsCheck(7, 2),
            AggsCheck(13, 1)
        )
        self.assertEquals(len(checks), len(result))
        for idx, check in enumerate(checks):
            to_check = result[idx]
            self.assertEquals(check, AggsCheck(**to_check))
