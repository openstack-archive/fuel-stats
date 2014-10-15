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

from analytics import config
from analytics.test.base import AggsCheck
from analytics.test.base import ElasticTest


class NodesDistribution(ElasticTest):

    def test_report(self):
        docs = [
            {
                'master_node_uid': 'x0',
                'allocated_nodes_num': 1,
                'unallocated_nodes_num': 4
            },
            {
                'master_node_uid': 'x1',
                'allocated_nodes_num': 7,
                'unallocated_nodes_num': 0
            },
            {
                'master_node_uid': 'x11',
                'allocated_nodes_num': 7,
                'unallocated_nodes_num': 0
            },
            {
                'master_node_uid': 'x12',
                'allocated_nodes_num': 5,
                'unallocated_nodes_num': 0
            },
            {
                'master_node_uid': 'x2',
                'allocated_nodes_num': 13,
                'unallocated_nodes_num': 10
            },
            {
                'master_node_uid': 'x4',
                'allocated_nodes_num': 0,
                'unallocated_nodes_num': 0
            },
            {
                'master_node_uid': 'x5',
                'allocated_nodes_num': 0,
                'unallocated_nodes_num': 2
            },
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE,
                          doc, id=doc['master_node_uid'])

        self.es.indices.refresh(config.INDEX_FUEL)

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

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=nodes_distribution)
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

        # range includes 'from', excludes 'to'
        nodes_ranges = {
            "size": 0,
            "aggs": {
                "nodes_ranges": {
                    "range": {
                        "field": "allocated_nodes_num",
                        "ranges": [
                            {"to": 5},
                            {"from": 5, "to": 10},
                            {"from": 10}
                        ]
                    }
                }
            }
        }
        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=nodes_ranges)
        expected = [
            {'key': '*-5.0', 'doc_count': 3},
            {'key': '5.0-10.0', 'doc_count': 3},
            {'key': '10.0-*', 'doc_count': 1},
        ]
        result = resp['aggregations']['nodes_ranges']['buckets']
        for idx, check in enumerate(expected):
            res = result[idx]
            self.assertEquals(AggsCheck(**check),
                              AggsCheck(
                                  key=res['key'],
                                  doc_count=res['doc_count']
                              ))
        self.assertEquals(3, result[0]['doc_count'])
        self.assertEquals('*-5.0', result[0]['key'])

    def test_clusters_by_nodes_num(self):
        docs = [
            {'master_node_uid': 'x0', 'clusters': [{'nodes_num': 1}]},
            {'master_node_uid': 'x1', 'clusters': [
                {'nodes_num': 1}, {'nodes_num': 2}]},
            {'master_node_uid': 'x2', 'clusters': [{'nodes_num': 0}]},
            {'master_node_uid': 'x3', 'clusters': [{'nodes_num': 2}]},
            {'master_node_uid': 'x4', 'clusters': [{'nodes_num': 1}]}
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE, doc,
                          id=doc['master_node_uid'])
        self.es.indices.refresh(config.INDEX_FUEL)

        # checking calculation
        clusters_by_nodes_num = {
            "size": 0,
            "aggs": {
                "clusters": {
                    "nested": {"path": "clusters"},
                    "aggs": {
                        "clusters_by_nodes_num": {
                            # calculating nodes num
                            "terms": {
                                "field": "clusters.nodes_num"
                            }
                        }
                    }
                }
            }
        }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=clusters_by_nodes_num)
        clusters = resp['aggregations']['clusters']
        result = clusters['clusters_by_nodes_num']['buckets']
        expected = [
            AggsCheck(1, 3),
            AggsCheck(2, 2),
            AggsCheck(0, 1)
        ]
        actual = [AggsCheck(**d) for d in result]
        self.assertListEqual(sorted(expected), sorted(actual))
