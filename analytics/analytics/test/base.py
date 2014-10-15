from collections import namedtuple
from analytics import config
from elasticsearch import Elasticsearch
from unittest2.case import TestCase


class BaseTest(TestCase):

    pass


class ElasticTest(BaseTest):

    INDEX_FUEL = config.INDEX_FUEL
    DOC_TYPE_INSTALLATION = config.DOC_TYPE_INSTALLATION

    es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200}])

    def setUp(self):
        super(ElasticTest, self).setUp()
        # cleaning index
        self.es.indices.delete(self.INDEX_FUEL, ignore=[404])
        self.es.indices.create(self.INDEX_FUEL)
        self.es.indices.put_mapping(
            config.DOC_TYPE_INSTALLATION,
            config.INDEXES_MAPPINGS[config.INDEX_FUEL],
            index=config.INDEX_FUEL
        )


AggsCheck = namedtuple('AggsCheck', ['key', 'doc_count'])
