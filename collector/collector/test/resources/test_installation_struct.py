from flask import json

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.common import consts
from collector.api.db.model import ActionLog


class TestInstallationStruct(DbTest):

    def test_not_allowed_methods(self):
        resp = self.get('/api/v1/installation_struct/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/installation_struct/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/installation_struct/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/installation_struct/', None)
        self.check_response_error(resp, 405)

    def test_validation_error(self):
        data = {'aid': 'x'}
        resp = self.post(
            '/api/v1/installation_struct/',
            {'installation_struct': data}
        )
        self.check_response_error(resp, code=400)
