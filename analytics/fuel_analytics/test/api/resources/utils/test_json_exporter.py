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
import json
import six

from fuel_analytics.test.api.resources.utils.inst_structure_test import \
    InstStructureTest
from fuel_analytics.test.api.resources.utils.oswl_test import \
    OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
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
        for param_name, param_value, expected in variants:
            req_params = '/?{0}={1}'.format(
                param_name, json.dumps(param_value))
            with app.test_request_context(req_params):
                self.assertDictEqual(
                    expected,
                    json_exporter.get_dict_param(name)
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

        for param_name, param_value, expected in variants:
            req_params = '/?{0}={1}'.format(
                param_name, json.dumps(param_value))

            with app.test_request_context(req_params):
                self.assertEqual(
                    expected,
                    json_exporter.get_paging_params()
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

        for expected in objs:
            # Checking objects to json serialization
            obj_json = json_exporter.row_as_serializable_dict(expected)
            json.dumps(obj_json)

            # Checking objects serialized properly
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

    def test_get_filtered_installation_infos(self):
        total_num = 10
        filtered_num = 4
        structs = self.get_saved_inst_structures(installations_num=total_num)
        for struct in structs[:filtered_num]:
            struct.is_filtered = True
        db.session.flush()

        with app.test_request_context():
            url = '/api/v1/json/installation_infos/filtered'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            result = json.loads(resp.data)

            self.assertEquals(filtered_num, result['paging_params']['total'])
            for struct in result['objs']:
                self.assertTrue(struct['is_filtered'])

    def test_get_db_summary(self):
        oswls = self.get_saved_oswls(100, consts.OSWL_RESOURCE_TYPES.volume)
        inst_infos = self.get_saved_inst_structs(
            oswls, is_filtered_values=(True, False, None))
        not_filtered_num = len(filter(lambda x: x.is_filtered is False,
                                      inst_infos))
        filtered_num = len(inst_infos) - not_filtered_num
        action_logs = self.get_saved_action_logs(inst_infos)
        expected = {
            'oswl_stats': {'total': len(oswls)},
            'installation_structures': {
                'total': len(inst_infos),
                'filtered': filtered_num,
                'not_filtered': not_filtered_num
            },
            'action_logs': {'total': len(action_logs)}
        }
        with app.test_request_context():
            url = '/api/v1/json/summary'
            resp = self.client.get(url)
            self.check_response_ok(resp)
            actual = json.loads(resp.data)
            self.assertEqual(expected, actual)
