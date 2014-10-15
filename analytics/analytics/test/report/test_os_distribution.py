import six

from analytics.test.base import ElasticTest


class OsDistribution(ElasticTest):

    def test_report(self):
        docs = [
            {
                'aid': 'x0',
                'clusters': [
                    {'release': {'os': 'CentOs'}
                    ,'status': 'a'
                    ,'os': 'x'}
                ]
            },
            {
                'aid': 'x1',
                'clusters': [
                    {'release': {'os': 'CentOs'}},
                    {'release': {'os': 'ubuntu'}},
                    {'release': {'os': 'UBUNTU'}},
                    {'release': {'os': 'Ubuntu'}
                    ,'status': 'b'}
                ]
            },
            {
                'aid': 'x11',
                'clusters': [
                    {'release': {'os': 'centos'}
                    ,'status': 'a'}
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
            self.es.index(self.INDEX_FUEL, self.DOC_TYPE_INSTALLATION, doc, id=doc['aid'])

        self.es.indices.refresh(self.INDEX_FUEL)

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
        # oses_distribution = {
        #     'size': 0,
        #     'aggs': {
        #         'oses_distribution': {
        #             'stats': {'field': 'aid'}
        #             # 'stats': {'field': 'clusters.nodes.os'}
        #         }
        #     }
        # }

        resp = self.es.search(index='fuel', doc_type='installation', body=oses_list)
        print "### resp", resp
        # result = resp['aggregations']['oses']['buckets']
        # oses = [d['key'] for d in result]
        # print "### result", oses
        # self.assertGreaterEqual(len(docs), len(result))
        # AggsCheck = namedtuple('AggsCheck', ['key', 'doc_count'])
        # checks = (
        #     AggsCheck(0, 2),
        #     AggsCheck(1, 1),
        #     AggsCheck(5, 1),
        #     AggsCheck(7, 2),
        #     AggsCheck(13, 1)
        # )
        # self.assertEquals(len(checks), len(result))
        # for idx, check in enumerate(checks):
        #     to_check = result[idx]
        #     self.assertEquals(check, AggsCheck(**to_check))
