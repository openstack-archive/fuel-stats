from flask import json
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from unittest2.case import TestCase

from collector.api import app
from collector.api.db import db
from collector.api.log import init_logger


Session = sessionmaker()


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


class DbTestCase(BaseTest):

    def setUp(self):
        super(DbTestCase, self).setUp()

        # connect to the database
        self.conn = db.engine.connect()

        # begin a non-ORM transaction
        self.trans = self.conn.begin()

        # bind an individual Session to the connection
        self.session = Session(bind=self.conn)

        # start the session in a SAVEPOINT...
        self.session.begin_nested()

        # then each time that SAVEPOINT ends, reopen it
        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                session.begin_nested()

    def tearDown(self):
        self.session.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.commit()

        # return connection to the Engine
        self.conn.close()

        super(DbTestCase, self).tearDown()