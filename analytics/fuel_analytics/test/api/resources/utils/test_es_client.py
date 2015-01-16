#    Copyright 2015 Mirantis, Inc.
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

from fuel_analytics.test.base import ElasticTest

from fuel_analytics.api.app import app
from fuel_analytics.api.resources.utils.es_client import ElasticSearchClient


class EsClientTest(ElasticTest):

    def test_fetch_all_data(self):
        installations_num = 160
        self.generate_data(installations_num=installations_num)

        query = {"query": {"match_all": {}}}
        es_client = ElasticSearchClient()
        doc_type = app.config['ELASTIC_DOC_TYPE_STRUCTURE']
        resp = es_client.fetch_all_data(query, doc_type,
                                        show_fields=('master_node_uid',),
                                        chunk_size=installations_num / 10 + 1)
        mn_uids = set([row['master_node_uid'] for row in resp])
        self.assertEquals(installations_num, len(mn_uids))

    def test_get_structures(self):
        installations_num = 100
        self.generate_data(installations_num=installations_num)
        es_client = ElasticSearchClient()
        resp = es_client.get_structures()
        mn_uids = set([row['master_node_uid'] for row in resp])
        self.assertEquals(installations_num, len(mn_uids))
