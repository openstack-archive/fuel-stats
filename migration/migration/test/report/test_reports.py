
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
from migration.test.base import ElasticTest


class Reports(ElasticTest):

    def test_nodes_distribution(self):
        structures = self.generate_data(installations_num=100)
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
        distrs = resp['aggregations']['nodes_distribution']['buckets']
        actual_distr = dict([(d['key'], d['doc_count']) for d in distrs])
        expected_distr = defaultdict(int)
        for structure in structures:
            expected_distr[structure['allocated_nodes_num']] += 1
        self.assertDictEqual(expected_distr, actual_distr)

    def test_envs_distribution(self):
        structures = self.generate_data(installations_num=100)
        envs_distribution = {
            "size": 0,
            "aggs": {
                "envs_distribution": {
                    "histogram": {
                        "field": "clusters_num",
                        "interval": 1
                    }
                }
            }
        }
        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=envs_distribution)
        distrs = resp['aggregations']['envs_distribution']['buckets']
        actual_distr = dict([(d['key'], d['doc_count']) for d in distrs])
        expected_distr = defaultdict(int)
        for structure in structures:
            expected_distr[structure['clusters_num']] += 1
        self.assertDictEqual(expected_distr, actual_distr)

    def test_installations_number(self):
        installations_num = 150
        self.generate_data(installations_num=installations_num)
        resp = self.es.count(index=config.INDEX_FUEL,
                             doc_type=config.DOC_TYPE_STRUCTURE)
        self.assertEquals(installations_num, resp['count'])

    def test_filtration(self):
        installations_num = 100
        structures = self.generate_data(installations_num=installations_num)
        statuses = ["operational", "error"]
        query = {
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
                                "attributes": {
                                    "nested": {
                                        "path": "clusters.attributes"
                                    },
                                    "aggs": {
                                        "libvirt_types": {
                                            "terms": {
                                                "field": "libvirt_type"
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
                              body=query)

        # checking filtered clusters num
        filtered_statuses = resp['aggregations']['clusters']['statuses']
        actual_clusters_num = filtered_statuses['doc_count']
        expected_clusters_num = 0
        for structure in structures:
            expected_clusters_num += len(
                filter(lambda c: c['status'] in statuses,
                       structure['clusters'])
            )
        self.assertEquals(expected_clusters_num, actual_clusters_num)

        # checking number of filtered libvirt types and clusters
        libvirt_types = filtered_statuses['attributes']['libvirt_types']
        self.assertEquals(
            expected_clusters_num,
            sum(d['doc_count'] for d in libvirt_types['buckets'])
        )

    def test_filtration_by_releases(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)

        # Fetching available releases
        query = {
            "size": 0,
            "aggs": {
                "releases": {
                    "terms": {
                        "field": "fuel_release.release"
                    }
                }
            }
        }
        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=query)
        releases_data = dict([(d['key'], d['doc_count']) for d in
                              resp['aggregations']['releases']['buckets']])

        # Adding filtration by the releases into libvirt distribution query
        statuses = ["operational", "error"]
        filter_by_release = six.iterkeys(releases_data).next()
        query = {
            "size": 0,
            "aggs": {
                "releases": {
                    "filter": {
                        "terms": {
                            "fuel_release.release": [filter_by_release]
                        }
                    },

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
                                        "attributes": {
                                            "nested": {
                                                "path": "clusters.attributes"
                                            },
                                            "aggs": {
                                                "libvirt_types": {
                                                    "terms": {
                                                        "field": "libvirt_type"
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
            }
        }
        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=query)
        # checking filtered clusters num
        filtered_releases = resp['aggregations']['releases']
        # checking releases are filtered
        self.assertEquals(releases_data[filter_by_release],
                          filtered_releases['doc_count'])
