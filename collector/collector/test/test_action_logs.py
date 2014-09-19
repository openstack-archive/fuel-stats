from collector.test.base import BaseTest, DbTestCase


class TestActionLogs(DbTestCase):

    def test_post(self):
        resp = self.post('/api/v1/action_logs', {'id': 1})
        self.check_response_ok(resp, code=201)

    def test_savepoints(self):
        from collector.api.db.model import ActionLog
        self.session.add(ActionLog(node_aid='xx', external_id=1))
        self.session.commit()