from collector.test.base import DbTest

from sqlalchemy.exc import IntegrityError

from collector.api.app import db
from collector.api.db.model import ActionLog


class TestModelActionLog(DbTest):

    def test_unique_constraints(self):
        db.session.add(ActionLog(node_aid='aid', external_id=1))
        db.session.add(ActionLog(node_aid='aid', external_id=1))
        self.assertRaises(IntegrityError, db.session.flush)

    def test_non_nullable_fields(self):
        db.session.add(ActionLog())
        self.assertRaises(IntegrityError, db.session.flush)

        db.session.add(ActionLog(node_aid='aid'))
        self.assertRaises(IntegrityError, db.session.flush)
