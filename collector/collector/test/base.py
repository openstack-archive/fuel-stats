from flask import json
from unittest2.case import TestCase

from collector.api import app


class BaseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        app.app.config.from_object('collector.api.config.Testing')

    def setUp(self):
        self.client = app.app.test_client()

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data),
                                content_type='application/json')

    def test_unknown_resource(self):
        resp = self.client.get('/xxx')
        print "### resp", resp

