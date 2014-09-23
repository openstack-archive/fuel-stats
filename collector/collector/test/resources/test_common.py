from collector.test.base import BaseTest


class TestCommon(BaseTest):

    def test_unknown_resource(self):
        resp = self.client.get('/xxx')
        self.check_response_error(resp, 404)
