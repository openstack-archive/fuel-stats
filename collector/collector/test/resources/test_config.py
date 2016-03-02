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

import copy
import mock

from collector.test.base import BaseTest

from collector.api.app import app
from collector.api.config import index_filtering_rules
from collector.api.config import packages_as_index


class TestConfig(BaseTest):

    def test_filtering_rules_indexed(self):
        release = '8.0'
        packages_0 = [1, 5, 2]
        packages_1 = [6, 4, 3]
        from_date_1 = '2016-03-01'
        packages_2 = []
        raw_rules = {
            release: [
                {'packages_list': packages_0},
                {'packages_list': packages_1, 'from_date': from_date_1},
                {'packages_list': packages_2, 'from_date': None}
            ]
        }

        expected_rules = {
            release: {
                packages_as_index(packages_0): None,
                packages_as_index(packages_1): from_date_1,
                packages_as_index(packages_2): None
            }
        }

        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': copy.deepcopy(raw_rules)}
        ):
            # Checking filtering rules before sorting
            actual_rules = app.config.get('FILTERING_RULES')
            actual_release_rules = actual_rules[release]
            for rule in raw_rules[release]:
                packages = packages_as_index(rule['packages_list'])
                self.assertNotIn(packages, actual_release_rules)

            # Checking filtering rules after sorting
            index_filtering_rules(app)
            actual_rules = app.config.get('FILTERING_RULES')
            self.assertEqual(expected_rules, actual_rules)

    def test_mix_packages_and_build_id(self):
        release_build_id = '7.0'
        build_id = 'build_id_0'

        release_mixed = '8.0'
        build_id_mixed = 'build_id_1'
        from_date = '2016-03-01'
        packages = [1, 5, 2]

        raw_rules = {
            release_mixed: [{'packages_list': packages},
                            {'build_id': build_id_mixed,
                             'from_date': from_date}],
            release_build_id: {build_id: None}
        }

        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': copy.deepcopy(raw_rules)}
        ):
            index_filtering_rules(app)
            actual_filtering_rules = app.config.get('FILTERING_RULES')

        expected_rules = {
            release_mixed: {
                packages_as_index(packages): None,
                build_id_mixed: from_date
            },
            release_build_id: {
                build_id: None
            }
        }
        self.assertEqual(expected_rules, actual_filtering_rules)

    def test_index_filtering_rules_idempotent(self):
        packages = ('a', 'b', 'c')
        release = '8.0'
        with mock.patch.dict(
            app.config,
            {'FILTERING_RULES': {release: {packages: None}}}
        ):
            index_filtering_rules(app)
            expected_rules = copy.copy(
                app.config.get('FILTERING_RULES')[release])
            index_filtering_rules(app)
            actual_rules = copy.copy(
                app.config.get('FILTERING_RULES')[release])
            self.assertIn(packages_as_index(packages), actual_rules)
            self.assertEqual(expected_rules, actual_rules)

    def test_index_filtering_rules(self):
        packages = ['z', 'x', 'a']
        self.assertEqual(tuple(sorted(packages)),
                         packages_as_index(packages))
