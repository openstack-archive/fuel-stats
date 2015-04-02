# -*- coding: utf-8 -*-

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

from fuel_analytics.test.api.resources.utils.inst_structure_test import \
    InstStructureTest
from fuel_analytics.test.api.resources.utils.oswl_test import \
    OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app


class JsonExporterTest(InstStructureTest, OswlTest, DbTest):

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
