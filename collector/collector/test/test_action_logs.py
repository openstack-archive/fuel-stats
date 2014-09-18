from collector.test.base import BaseTest


class TestActionLogs(BaseTest):
    def test_post(self):
        resp = self.post('/api/v1/action_logs', {'id': 1})
        print "### resp.status_code", resp.status_code
        print "### resp.headers", resp.headers
        print "### resp.data", resp.data
        print "### resp", resp

        # resp = self.client.get('/api/v1/action_logs')
        # # from collector.api.app import api
        # # print "### resources", api.resources
        # print "### resp.status_code", resp.status_code
        # print "### resp.headers", resp.headers
        # print "### resp.data", resp.data