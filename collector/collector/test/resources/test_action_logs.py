from collector.test.base import DbTestCase


class TestActionLogs(DbTestCase):

    def test_not_allowed_methods(self):
        resp = self.get('/api/v1/action_logs/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/action_logs/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/action_logs/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/action_logs/', None)
        self.check_response_error(resp, 405)

    def test_post(self):
        resp = self.post('/api/v1/action_logs/', {'id': 1})
        self.check_response_ok(resp, code=201)

