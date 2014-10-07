from elasticsearch import Elasticsearch

from unittest2.case import TestCase


class BaseTest(TestCase):

    pass


class ElasticTest(BaseTest):

    INDEX_FUEL = 'fuel'
    DOC_TYPE_INSTALLATION = 'installation'

    es = Elasticsearch(hosts=[{'host': 'localhost', 'port': 9200}])
