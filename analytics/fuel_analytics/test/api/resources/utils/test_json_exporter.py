#    Copyright 2015 Mirantis, Inc.
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

import datetime
from flask import request
import json
import mock
import six

from fuel_analytics.test.api.resources.utils.inst_structure_test import \
    InstStructureTest
from fuel_analytics.test.api.resources.utils.oswl_test import \
    OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db import model
from fuel_analytics.api.resources import json_exporter


class JsonExporterTest(InstStructureTest, OswlTest, DbTest):

    def test_jsonify_collection(self):
        variants = [[], [{}], [{'a': 'b'}, {'c': 'd'}]]
        for variant in variants:
            it = iter(variant)
            jsonified = six.text_type(''.join(
                json_exporter._jsonify_collection(it)))
            restored = json.loads(jsonified)
            self.assertItemsEqual(variant, restored)

    def test_get_installation_info_not_found(self):
        with app.test_request_context():
            resp = self.client.get('/api/v1/json/installation_info/xxxx')
            self.check_response_error(resp, 404)

    def test_get_installation_info(self):
        structs = self.get_saved_inst_structures(installations_num=10)
        with app.test_request_context():
            for struct in structs:
                url = '/api/v1/json/installation_info/{}'.format(
                    struct.master_node_uid)
                resp = self.client.get(url)
                self.check_response_ok(resp)
                # Checking response is json
                json.loads(resp.data)

    def test_get_oswls(self):
        num = 10
        for resource_type in self.RESOURCE_TYPES:
            oswls = self.get_saved_oswls(num, resource_type)
            structs = self.get_saved_inst_structs(oswls)
            with app.test_request_context():
                for struct in structs:
                    url = '/api/v1/json/oswls/{}'.format(
                        struct.master_node_uid)
                    resp = self.client.get(url)
                    self.check_response_ok(resp)
                    # Checking response is json
                    json.loads(resp.data)

    def test_get_oswls_by_resource_type(self):
        num = 10
        for resource_type in self.RESOURCE_TYPES:
            oswls = self.get_saved_oswls(num, resource_type)
            structs = self.get_saved_inst_structs(oswls)
            with app.test_request_context():
                for struct in structs:
                    url = '/api/v1/json/oswls/{}/{}'.format(
                        struct.master_node_uid, resource_type)
                    resp = self.client.get(url)
                    self.check_response_ok(resp)
                    # Checking response is json
                    json.loads(resp.data)

    def test_get_action_logs(self):
        structs = self.get_saved_inst_structures(installations_num=10)
        self.get_saved_action_logs(structs)
        with app.test_request_context():
            for struct in structs:
                url = '/api/v1/json/action_logs/{}'.format(
                    struct.master_node_uid)
                resp = self.client.get(url)
                self.check_response_ok(resp)
                # Checking response is json
                json.loads(resp.data)

    def test_get_dict_param(self):
        # Pairs of param_name, param_value, expected
        name = 'param_name'
        variants = (
            ('wrong_name', {}, {}),
            (name, {}, {}), (name, None, {}), (name, 'a', {}),
            (name, 1, {}), (name, [], {}), (name, (), {}),
            (name, {'a': 'b'}, {'a': 'b'})
        )
        with app.test_request_context():
            for param_name, param_value, expected in variants:
                with mock.patch.object(request, 'args',
                                       {param_name: param_value}):
                    self.assertDictEqual(
                        json_exporter.get_dict_param(name),
                        expected
                    )

    def test_get_paging_params(self):
        name = 'paging_params'
        limit_default = app.config.get('JSON_DB_DEFAULT_LIMIT')
        variants = (
            (name, {}, {'limit': limit_default, 'offset': 0}),
            (name, [], {'limit': limit_default, 'offset': 0}),
            (name, 4, {'limit': limit_default, 'offset': 0}),
            ('wrong_name', 4, {'limit': limit_default, 'offset': 0}),
            (name, {'trash': 'x'}, {'limit': limit_default, 'offset': 0}),
            (name, {'limit': limit_default + 1}, {'limit': limit_default + 1,
                                                  'offset': 0}),
            (name, {'limit': limit_default + 1, 'offset': 50},
             {'limit': limit_default + 1, 'offset': 50}),
        )

        with app.test_request_context():
            for param_name, param_value, expected in variants:
                with mock.patch.object(request, 'args',
                                       {param_name: param_value}):
                    self.assertDictEqual(
                        json_exporter.get_paging_params(),
                        expected
                    )

    def test_row_as_serializable_dict(self):
        dt_now = datetime.datetime.utcnow()
        d_now = dt_now.date()
        t_now = dt_now.time()
        objs = [
            model.InstallationStructure(
                id=0, master_node_uid='xx', structure={'a': [], 'b': 'c'},
                creation_date=dt_now, modification_date=dt_now),
            model.ActionLog(id=0, master_node_uid='yy', external_id=33,
                            body={'c': 4}),
            model.OpenStackWorkloadStats(
                id=0, master_node_uid='zz', external_id=45, cluster_id=44,
                created_date=d_now, updated_time=t_now,
                resource_type='vm', resource_data={},
                resource_checksum='chk'
            )
        ]

        # Checking objects to json serialization
        objs_json = []
        for obj in objs:
            d = json_exporter.row_as_serializable_dict(obj)
            json.dumps(d)
            objs_json.append(d)

        # Checking objects serialized properly
        for idx, obj_json in enumerate(objs_json):
            expected = objs[idx]
            actual = expected.__class__(**obj_json)

            # Saving object for proper types conversion
            db.session.add(actual)
            db.session.commit()

            # Checking SqlAlchemy objects equality
            for c in expected.__table__.columns:
                column_name = c.name
                self.assertEquals(
                    getattr(expected, column_name),
                    getattr(actual, column_name)
                )
