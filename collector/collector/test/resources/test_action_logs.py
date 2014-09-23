from collector.test.base import DbTestCase

from collector.api.app import db
from collector.api.db.model import ActionLogs


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

    def test_empty_action_logs_post(self):
        resp = self.post('/api/v1/action_logs/', {'action_logs': []})
        self.check_response_ok(resp, code=201)

    def test_post(self):
        node_aid = 'x'
        expected_logs = [
            {'node_aid': node_aid, 'external_id': 1},
            {'node_aid': node_aid, 'external_id': 2},
            {'node_aid': node_aid, 'external_id': 3}
        ]
        resp = self.post(
            '/api/v1/action_logs/',
            {'action_logs': expected_logs}
        )
        self.check_response_ok(resp, code=201)

        actual_logs = db.session.query(ActionLogs).filter(ActionLogs.node_aid==node_aid).all()
        self.assertEquals(len(expected_logs), len(actual_logs))
        self.assertListEqual(
            sorted([l['external_id'] for l in expected_logs]),
            sorted([l.external_id for l in actual_logs])
        )
