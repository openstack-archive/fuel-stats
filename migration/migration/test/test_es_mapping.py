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


class ElasticsearchMapping(ElasticTest):

    def test_master_node_uid_not_analyzed(self):
        docs = [
            {'master_node_uid': 'x0'},
            {'master_node_uid': 'x0-1'},
            {'master_node_uid': 'x0_2'},
            {'master_node_uid': 'x03'},
            {'master_node_uid': 'x1'},
            {'master_node_uid': 'x1 1'},
        ]

        for doc in docs:
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE, doc,
                          id=doc['master_node_uid'])
        self.es.indices.refresh(config.INDEX_FUEL)

        # checking master_node_uid tokenizer
        master_node_uids = {
            'size': 0,
            'aggs': {
                'structs': {
                    'terms': {
                        'field': 'master_node_uid'
                    }
                }
            }
        }

        resp = self.es.search(index=config.INDEX_FUEL,
                              doc_type=config.DOC_TYPE_STRUCTURE,
                              body=master_node_uids)
        result = resp['aggregations']['structs']['buckets']
        # checking that master_node_uids with whitespaces and
        # non-literal symbols didn't split
        self.assertEquals(len(docs), len(result))

    def test_mixed_values_in_list_migration(self):
        doc = {
            'master_node_uid': 'x1',
            'additional_info': {
                'request_data': {
                    'data': {
                        'settings': {
                            'statistics': {
                                'company': {'restrictions': [
                                    'string', {'a': 'b'}]},
                            }
                        }
                    }
                }
            }
        }
        self.es.index(config.INDEX_FUEL, config.DOC_TYPE_ACTION_LOGS, doc,
                      id=doc['master_node_uid'])
