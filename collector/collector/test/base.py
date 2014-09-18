from flask import json
from unittest2.case import TestCase

from collector.api import app
from collector.api.log import init_logger


class BaseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        app.app.config.from_object('collector.api.config.Testing')
        init_logger()

    def setUp(self):
        self.client = app.app.test_client()

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data),
                                content_type='application/json')

    def check_response_ok(self, resp, code=200):
        self.assertEquals(code, resp.status_code)
        d = json.loads(resp.data)
        self.assertEquals('ok', d['status'])

    def check_response_error(self, resp, code):
        self.assertEquals(code, resp.status_code)
        d = json.loads(resp.data)
        self.assertEquals('error', d['status'])

    def test_unknown_resource(self):
        resp = self.client.get('/xxx')
        self.check_response_error(resp, 404)

