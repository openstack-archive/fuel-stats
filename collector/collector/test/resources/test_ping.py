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

from collector.test.base import BaseTest


class TestPing(BaseTest):

    def test_not_allowed_methods(self):
        resp = self.post('/api/v1/ping/', None)
        self.check_response_error(resp, 405)
        resp = self.delete('/api/v1/ping/')
        self.check_response_error(resp, 405)
        resp = self.patch('/api/v1/ping/', None)
        self.check_response_error(resp, 405)
        resp = self.put('/api/v1/ping/', None)
        self.check_response_error(resp, 405)

    def test_get(self):
        resp = self.get('/api/v1/ping/', None)
        self.check_response_ok(resp, code=200)
