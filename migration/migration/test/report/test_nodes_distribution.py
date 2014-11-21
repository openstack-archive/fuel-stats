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

from migration import config
from migration.test.base import ElasticTest


class NodesDistribution(ElasticTest):

    def test_report(self):
        structures = self.generate_data()
        statuses = ["operational", "error"]
        ranges = [
            {"to": 75},
            {"from": 75, "to": 85},
            {"from": 85}
        ]
        nodes_distribution = {
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
                                "nodes_ranges": {
                                    "range": {
                                        "field": "nodes_num",
                                        "ranges": ranges
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
                              body=nodes_distribution)
        filtered_statuses = resp['aggregations']['clusters']['statuses']
        nodes_ranges = filtered_statuses['nodes_ranges']['buckets']
        actual_ranges = [d['doc_count'] for d in nodes_ranges]

        expected_envs_num = 0
        expected_ranges = [0] * len(ranges)
        for structure in structures:
            clusters_in_statuses = filter(lambda c: c['status'] in statuses,
                                          structure['clusters'])
            expected_envs_num += len(clusters_in_statuses)
            for cluster in clusters_in_statuses:
                for idx, r in enumerate(ranges):
                    f = r.get('from', 0)
                    t = r.get('to')
                    nodes_num = cluster['nodes_num']
                    if nodes_num >= f and (t is None or nodes_num < t):
                        expected_ranges[idx] += 1
                        continue
        self.assertListEqual(expected_ranges, actual_ranges)
