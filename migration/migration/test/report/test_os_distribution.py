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

from collections import defaultdict
import six

from migration import config
from migration.test.base import AggsCheck
from migration.test.base import ElasticTest


class OsDistribution(ElasticTest):

    def test_os_analyzer(self):
        docs = [
            {
                'master_node_uid': 'x0',
                'clusters': [
                    {'release': {'os': 'CentOs'}}
                ]
            },
            {
                'master_node_uid': 'x1',
                'clusters': [
                    {'release': {'os': 'CentOs Custom Version'}},
                    {'release': {'os': 'ubuntu'}},
                    {'release': {'os': 'UbuNtu'}},
                    {'release': {'os': 'centos'}}
                ]
            },
            {
                'master_node_uid': 'x11',
                'clusters': [
                    {'release': {'os': 'Ubuntu'}}
                ]
            },
            {
                'master_node_uid': 'x12',
                'clusters': []
            },
            {
                'master_node_uid': 'x5',
                'clusters': [
                    {'release': {'os': 'Solaris'}}
                ]
            },
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE,
                          doc, id=doc['master_node_uid'])

        self.es.indices.refresh(config.INDEX_FUEL)

        # nodes oses distribution request
        oses_list = {
            "size": 0,
            "aggs": {
                "clusters": {
                    "nested": {
                        "path": "clusters"
                    },
                    "aggs": {
                        "release": {
                            "nested": {
                                "path": "clusters.release"
                            },
                            "aggs": {
                                "oses": {
                                    "terms": {
                                        "field": "os"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=oses_list)
        result = resp['aggregations']['clusters']['release']['oses']['buckets']
        checks = (
            AggsCheck('centos', 2),
            AggsCheck('centos custom version', 1),
            AggsCheck('ubuntu', 3),
            AggsCheck('solaris', 1)
        )
        self.assertListEqual(
            sorted(checks),
            sorted(AggsCheck(**d) for d in result)
        )

    def test_report(self):
        structures = self.generate_data()
        statuses = ["operational", "error"]
        # nodes oses distribution request
        oses_list = {
            "size": 0,
            "aggs": {
                "clusters": {
                    "nested": {
                        "path": "clusters"
                    },
                    "aggs": {
                        "statuses": {
                            "filter": {
                                "terms": {"status": statuses}
                            },
                            "aggs": {
                                "release": {
                                    "nested": {
                                        "path": "clusters.release"
                                    },
                                    "aggs": {
                                        "oses": {
                                            "terms": {
                                                "field": "os"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=oses_list)
        filtered_clusters = resp['aggregations']['clusters']['statuses']
        result = filtered_clusters['release']['oses']['buckets']
        actual_oses = dict([(d['key'], d['doc_count']) for d in result])

        expected_oses = defaultdict(int)
        expected_clusters_num = 0
        for structure in structures:
            clusters_in_statuses = filter(lambda c: c['status'] in statuses,
                                          structure['clusters'])
            expected_clusters_num += len(clusters_in_statuses)
            for cluster in clusters_in_statuses:
                os = str.lower(cluster['release']['os'])
                expected_oses[os] += 1

        # checking aggregation result
        self.assertDictEqual(expected_oses, actual_oses)

        # checking clusters are filtered
        self.assertEquals(expected_clusters_num,
                          sum(six.itervalues(actual_oses)))
