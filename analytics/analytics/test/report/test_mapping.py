from analytics.test.base import ElasticTest


class Mapping(ElasticTest):

    def setUp(self):
        super(Mapping, self).setUp()

    def test_aid_not_analyzed(self):
        docs = [
            {'aid': 'x0'},
            {'aid': 'x0-1'},
            {'aid': 'x0_2'},
            {'aid': 'x03'},
            {'aid': 'x1'},
            {'aid': 'x1 1'},
        ]

        for doc in docs:
            self.es.index(self.INDEX_FUEL, self.DOC_TYPE_INSTALLATION, doc, id=doc['aid'])
        self.es.indices.refresh(self.INDEX_FUEL)

        # checking aid tokenizer
        aids = {
            "size": 0,
            "aggs": {
                "aids": {
                    "terms": {
                        "field": "aid"
                    }
                }
            }
        }

        resp = self.es.search(index='fuel', doc_type='installation', body=aids)
        result = resp['aggregations']['aids']['buckets']
        # checking that aids with whitespaces and non-literal symbols are not split
        self.assertEquals(len(docs), len(result))
