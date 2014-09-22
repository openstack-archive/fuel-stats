from sqlalchemy.exc import IntegrityError

from collector.api.db.model import ActionLogs
from collector.test.base import DbTestCase


class TestModelActionLog(DbTestCase):

    def test_unique_constraints(self):
        self.session.add(ActionLogs(node_aid='aid', external_id=1))
        self.session.add(ActionLogs(node_aid='aid', external_id=1))
        self.assertRaises(IntegrityError, self.session.flush)

    def test_non_nullable_fields(self):
        self.session.add(ActionLogs())
        self.assertRaises(IntegrityError, self.session.flush)
        self.session.rollback()

        self.session.add(ActionLogs(node_aid='aid'))
        self.assertRaises(IntegrityError, self.session.flush)
        self.session.rollback()
