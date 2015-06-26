
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
        # Generating not filtered data
        installations_num = 150
        installations = self.generate_data(
            installations_num=installations_num,
            is_filtered_values=(None, False)
        )
        # Generating filtered data
        self.generate_data(
            installations_num=70,
            is_filtered_values=(True,)
        )
        release = "6.0-ga"
        query = {
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "should": [
                                {"term": {"is_filtered": False}},
                                {"missing": {"field": "is_filtered"}},
                            ],
                            "must": {
                                "terms": {
                                    "fuel_release.release": [release]
                                }
                            }
                        }
                    }
                }
            }
        }
        resp = self.es.count(index=config.INDEX_FUEL,
                             doc_type=config.DOC_TYPE_STRUCTURE,
                             body=query)
        inst_count = len(filter(
            lambda x: x['fuel_release']['release'] == release, installations))
        self.assertEquals(inst_count, resp['count'])

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

    def _get_releases_data(self):
        # Fetching available releases info
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
        return dict([(d['key'], d['doc_count']) for d in
                     resp['aggregations']['releases']['buckets']])

    def _query_libvirt_distribution(self):
        statuses = ["operational", "error"]
        return {
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

    def _query_filter_by_release(self, releases, query):
        return {
            "releases": {
                "filter": {
                    "terms": {
                        "fuel_release.release": releases
                    }
                },
                "aggs": query
            }
        }

    def _query_filter_by_is_filtered(self, query):
        return {
            "is_filtered": {
                "filter": {
                    "bool": {
                        "should": [
                            {"term": {"is_filtered": False}},
                            {"missing": {"field": "is_filtered"}},
                        ]
                    }
                },
                "aggs": query
            }
        }

    def test_filtration_by_releases(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)

        # Adding filtration by the releases into libvirt distribution query
        releases_data = self._get_releases_data()
        filter_by_release = six.iterkeys(releases_data).next()
        query = {
            "size": 0,
            "aggs": self._query_filter_by_release(
                [filter_by_release], self._query_libvirt_distribution())
        }
        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=query)
        # checking filtered clusters num
        filtered_releases = resp['aggregations']['releases']
        # checking releases are filtered
        self.assertEquals(releases_data[filter_by_release],
                          filtered_releases['doc_count'])

    def test_filtration_by_is_filtered(self):
        # Query for fetching libvirt distribution
        libvirt_query = self._query_libvirt_distribution()

        # Query for filtration by is_filtered
        query = {
            "size": 0,
            "aggs": self._query_filter_by_is_filtered(libvirt_query)
        }

        # Checking filtered docs aren't fetched
        filtered_num = 15
        self.generate_data(installations_num=filtered_num,
                           is_filtered_values=(True,))

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=query)
        docs = resp['aggregations']['is_filtered']
        self.assertEqual(0, docs['doc_count'])

        # Checking false filtered docs are fetched
        not_filtered_num = 20
        self.generate_data(installations_num=not_filtered_num,
                           is_filtered_values=(False,))

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=query)
        docs = resp['aggregations']['is_filtered']
        self.assertEqual(not_filtered_num, docs['doc_count'])

        # Checking None filtered docs are fetched
        none_filtered_num = 25
        self.generate_data(installations_num=none_filtered_num,
                           is_filtered_values=(None,))

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=query)
        docs = resp['aggregations']['is_filtered']
        self.assertEqual(not_filtered_num + none_filtered_num,
                         docs['doc_count'])
