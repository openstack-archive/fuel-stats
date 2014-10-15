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

from collections import namedtuple
from elasticsearch import Elasticsearch
from unittest2.case import TestCase

from analytics import config


class BaseTest(TestCase):

    pass


class ElasticTest(BaseTest):

    es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200}])

    def setUp(self):
        super(ElasticTest, self).setUp()
        # cleaning index
        self.es.indices.delete(config.INDEX_FUEL, ignore=[404])

        settings = {
            'settings': {
                'analysis': config.INDEXES_ANALYSIS[config.INDEX_FUEL],
            },
            'mappings': config.INDEXES_MAPPINGS[config.INDEX_FUEL]
        }
        self.es.indices.create(config.INDEX_FUEL, body=settings)


AggsCheck = namedtuple('AggsCheck', ['key', 'doc_count'])
