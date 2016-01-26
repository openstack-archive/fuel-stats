#    Copyright 2016 Mirantis, Inc.
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

import mock

from collector.test.base import BaseTest

from collector.api.app import app
from collector.api.config import index_filtering_rules
from collector.api.config import normalize_build_info


class TestConfig(BaseTest):

    def test_filtering_rules_indexed(self):
        build_id = 'build_id_0'
        filtering_rules = {(3, 2, 1): None, (2, 1): '2016-01-26',
                           'build_id': build_id}
        release = '8.0'
        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: filtering_rules.copy()}}
        ):
            # Checking filtering rules before sorting
            actual_filtering_rules = app.config.get('FILTERING_RULES')[release]
            for packages, from_dt in filtering_rules.iteritems():
                if isinstance(packages, tuple):
                    self.assertNotIn(tuple(sorted(packages)),
                                     actual_filtering_rules)
                    self.assertIn(packages, actual_filtering_rules)

            # Checking filtering rules after sorting
            index_filtering_rules(app)
            actual_filtering_rules = app.config.get('FILTERING_RULES')[release]
            for packages, from_dt in filtering_rules.iteritems():
                if isinstance(packages, tuple):
                    self.assertIn(tuple(sorted(packages)),
                                  actual_filtering_rules)
                    self.assertNotIn(packages, actual_filtering_rules)
            self.assertEqual(build_id, actual_filtering_rules['build_id'])

    def test_normalize_build_info(self):
        build_id = '2016-xxx.yyy'
        self.assertEqual(build_id, normalize_build_info(build_id))
        packages = ['z', 'x', 'a']
        self.assertEqual(tuple(sorted(packages)),
                         normalize_build_info(packages))
