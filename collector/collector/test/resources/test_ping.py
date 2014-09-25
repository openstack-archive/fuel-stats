from collector.test.base import BaseTest


class TestPing(BaseTest):

    def test_not_allowed_methods(self):
        resp = self.post('/api/v1/ping/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/ping/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/ping/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/ping/', None)
        self.check_response_error(resp, 405)

    def test_get(self):
        resp = self.get('/api/v1/ping/', None)
        self.check_response_ok(resp, code=200)
