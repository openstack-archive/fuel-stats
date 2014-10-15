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
from analytics.test.base import ElasticTest


class Mapping(ElasticTest):

    def setUp(self):
        super(Mapping, self).setUp()

    def test_aid_not_analyzed(self):
        docs = [
            {'aid': 'x0'},
            {'aid': 'x0-1'},
            {'aid': 'x0_2'},
            {'aid': 'x03'},
            {'aid': 'x1'},
            {'aid': 'x1 1'},
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE, doc,
                          id=doc['aid'])
        self.es.indices.refresh(config.INDEX_FUEL)

        # checking aid tokenizer
        aids = {
            "size": 0,
            "aggs": {
                "aids": {
                    "terms": {
                        "field": "aid"
                    }
                }
            }
        }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE, body=aids)
        result = resp['aggregations']['aids']['buckets']
        # checking that aids with whitespaces and non-literal symbols
        # didn't split
        self.assertEquals(len(docs), len(result))

    def test_nodes_num_calculation(self):
        docs = [
            {'aid': 'x0', 'clusters': [{'nodes_num': 1}]},
            {'aid': 'x1', 'clusters': [{'nodes_num': 1}, {'nodes_num': 2}]},
            {'aid': 'x2', 'clusters': [{'nodes_num': 0}]},
            {'aid': 'x3', 'clusters': [{'nodes_num': 2}]},
            {'aid': 'x4', 'clusters': [{'nodes_num': 1}]}
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE, doc,
                          id=doc['aid'])
        self.es.indices.refresh(config.INDEX_FUEL)

        # checking calculation
        aids = {
            "size": 0,
            "aggs": {
                "clusters": {
                    # going to the nested document
                    "nested": {"path": "clusters"},
                    "aggs": {
                        "nodes_num": {
                            # calculating nodes num
                            "sum": {
                                "field": "clusters.nodes_num"
                            }
                        }
                    }
                }
            }
        }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE, body=aids)
        result = resp['aggregations']['clusters']
        self.assertEquals(6, result['doc_count'])
        self.assertEquals(7, result['nodes_num']['value'])

    def test_dynamic_nodes_num_calculation(self):
        docs = [
            {'aid': 'x0', 'clusters': [{'nodes_num': 1}]},
            {'aid': 'x1', 'clusters': [{'nodes_num': 1}, {'nodes_num': 2}]},
            {'aid': 'x2', 'clusters': [{'nodes_num': 0}]},
            {'aid': 'x3', 'clusters': [{'nodes_num': 2}]},
            {'aid': 'x4', 'clusters': [{'nodes_num': 1}]}
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE, doc,
                          id=doc['aid'])
        self.es.indices.refresh(config.INDEX_FUEL)

        mapping = self.es.indices.get_mapping(index=config.INDEX_FUEL)
        import json
        print "### mapping", json.dumps(mapping)

        clusters_count = {
            "aggregations": {
                "clusters_count": {
                    "nested": {
                        "path": "clusters"
                    },
                    "aggregations": {
                        "value_count": {
                            "sum": {
                                "field": "clusters",
                                "script": "doc.values.length"
                            }
                        }
                    }
                }
            },
            "size": 0
        }
        # clusters_count = {
        #     "aggs": {
        #         "value_count": {
        #             "sum": {
        #                 "field": "clusters",
        #                 "script": "doc['clusters'].values.length"
        #             }
        #         }
        #     },
        #     "size": 0
        # }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE, body=clusters_count)
        print "### resp", resp
