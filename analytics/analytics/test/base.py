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

from unittest2.case import TestCase

from analytics.api.app import app
from analytics.api.log import init_logger

# Configuring app for the test environment
app.config.from_object('analytics.api.config.Testing')
init_logger()

from migration.test.base import ElasticTest as MigrationElasticTest


class BaseTest(TestCase):

    def setUp(self):
        super(BaseTest, self).setUp()
        self.client = app.test_client()

    def check_response_ok(self, resp, codes=(200, 201)):
        self.assertIn(resp.status_code, codes)

    def check_response_error(self, resp, code):
        self.assertEquals(code, resp.status_code)


class ElasticTest(MigrationElasticTest):
    pass
