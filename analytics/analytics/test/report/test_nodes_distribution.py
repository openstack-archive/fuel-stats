from analytics.test.base import AggsCheck
from analytics.test.base import ElasticTest


class NodesDistribution(ElasticTest):

    def test_report(self):
        docs = [
            {
                'aid': 'x0',
                'allocated_nodes_num': 1,
                'unallocated_nodes_num': 4
            },
            {
                'aid': 'x1',
                'allocated_nodes_num': 7,
                'unallocated_nodes_num': 0
            },
            {
                'aid': 'x11',
                'allocated_nodes_num': 7,
                'unallocated_nodes_num': 0
            },
            {
                'aid': 'x12',
                'allocated_nodes_num': 5,
                'unallocated_nodes_num': 0
            },
            {
                'aid': 'x2',
                'allocated_nodes_num': 13,
                'unallocated_nodes_num': 10
            },
            {
                'aid': 'x4',
                'allocated_nodes_num': 0,
                'unallocated_nodes_num': 0
            },
            {
                'aid': 'x5',
                'allocated_nodes_num': 0,
                'unallocated_nodes_num': 2
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
