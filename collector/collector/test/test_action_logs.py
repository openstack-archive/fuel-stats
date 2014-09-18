from collector.test.base import BaseTest


class TestActionLogs(BaseTest):
    def test_post(self):
        resp = self.post('/api/v1/action_logs', {'id': 1})
        self.check_response_ok(resp, code=201)
