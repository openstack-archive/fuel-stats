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


class OsDistribution(ElasticTest):

    def test_report(self):
        docs = [
            {
                'aid': 'x0',
                'clusters': [
                    {'release': {'os': 'CentOs'}}
                ]
            },
            {
                'aid': 'x1',
                'clusters': [
                    {'release': {'os': 'CentOs Custom Version'}},
                    {'release': {'os': 'Ubuntu'}},
                    {'release': {'os': 'Ubuntu'}},
                    {'release': {'os': 'CentOs'}}
                ]
            },
            {
                'aid': 'x11',
                'clusters': [
                    {'release': {'os': 'Ubuntu'}}
                ]
            },
            {
                'aid': 'x12',
                'clusters': []
            },
            {
                'aid': 'x5',
                'clusters': [
                    {'release': {'os': 'Solaris'}}
                ]
            },
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE,
                          doc, id=doc['aid'])

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
            AggsCheck('CentOs', 2),
            AggsCheck('CentOs Custom Version', 1),
            AggsCheck('Ubuntu', 3),
            AggsCheck('Solaris', 1)
        )
        self.assertListEqual(
            sorted(checks),
            sorted(AggsCheck(**d) for d in result)
        )
