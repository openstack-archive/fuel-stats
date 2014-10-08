#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from flask import json

from collector.test.base import DbTest

from collector.api.app import db
from collector.api.db.model import InstallationStruct


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
        wrong_data_sets = [
            {'installation_struct': {'aid': 'x'}},
            None,
            {}
        ]
        for data in wrong_data_sets:
            resp = self.post(
                '/api/v1/installation_struct/',
                data
            )
            self.check_response_error(resp, code=400)

    def test_post(self):
        aid = 'x'
        struct = {
            'aid': aid,
            'allocated_nodes_num': 4,
            'unallocated_nodes_num': 4,
            'clusters_num': 2,
            'clusters': [
                {
                    'id': 29,
                    'nodes_num': 3,
                    'nodes': [
                        {'id': 33, 'roles': ['a', 'b', 'c']},
                        {'id': 34, 'roles': ['b', 'c']},
                        {'id': 35, 'roles': ['c']}
                    ]
                },
                {
                    'id': 32,
                    'nodes_num': 1,
                    'nodes': [
                        {'id': 42, 'roles': ['s']}
                    ]
                },
            ]
        }
        resp = self.post(
            '/api/v1/installation_struct/',
            {'installation_struct': struct}
        )
        self.check_response_ok(resp, code=201)
        obj = db.session.query(InstallationStruct).filter(
            InstallationStruct.aid == aid).one()
        self.assertEquals(json.dumps(struct), obj.struct)
        self.assertIsNotNone(obj.creation_date)
        self.assertIsNone(obj.modification_date)

    def test_post_update(self):
        aid = 'xx'
        struct = {
            'aid': aid,
            'allocated_nodes_num': 0,
            'unallocated_nodes_num': 0,
            'clusters_num': 0,
            'clusters': []
        }
        resp = self.post(
            '/api/v1/installation_struct/',
            {'installation_struct': struct}
        )
        self.check_response_ok(resp, code=201)
        obj_new = db.session.query(InstallationStruct).filter(
            InstallationStruct.aid == aid).one()
        self.assertEquals(json.dumps(struct), obj_new.struct)
        self.assertIsNotNone(obj_new.creation_date)
        self.assertIsNone(obj_new.modification_date)

        struct['unallocated_nodes_num'] = 5
        resp = self.post(
            '/api/v1/installation_struct/',
            {'installation_struct': struct}
        )
        self.check_response_ok(resp, code=201)
        obj_upd = db.session.query(InstallationStruct).filter(
            InstallationStruct.aid == aid).one()
        self.assertEquals(json.dumps(struct), obj_upd.struct)
        self.assertIsNotNone(obj_upd.creation_date)
        self.assertIsNotNone(obj_upd.modification_date)
