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

from datetime import datetime
from datetime import timedelta

from fuel_analytics.test.api.resources.utils.oswl_test import OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
from fuel_analytics.api.db.model import ActionLog
from fuel_analytics.api.errors import DateExtractionError
from fuel_analytics.api.resources import csv_exporter as ce
from fuel_analytics.api.resources.csv_exporter import extract_date
from fuel_analytics.api.resources.csv_exporter import get_action_logs
from fuel_analytics.api.resources.csv_exporter import get_from_date
from fuel_analytics.api.resources.csv_exporter import get_inst_structures
from fuel_analytics.api.resources.csv_exporter import get_inst_structures_query
from fuel_analytics.api.resources.csv_exporter import get_oswls_query
from fuel_analytics.api.resources.csv_exporter import get_resources_types
from fuel_analytics.api.resources.csv_exporter import get_to_date
from fuel_analytics.api.resources.utils.stats_to_csv import ActionLogInfo
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv


class CsvExporterTest(OswlTest, DbTest):

    def test_get_oswls_query(self):
        num = 2
        for resource_type in self.RESOURCE_TYPES:
            # Fetching oswls count
            count_before = get_oswls_query(resource_type).count()

            # Generating oswls without installation info
            oswls = self.get_saved_oswls(num, resource_type)

            # Checking count of fetched oswls is not changed
            count_after = get_oswls_query(resource_type).count()
            self.assertEqual(count_before, count_after)

            # Saving inst structures
            self.get_saved_inst_structs(oswls)

            # Checking count of fetched oswls is changed
            count_after = get_oswls_query(resource_type).count()
            self.assertEqual(num + count_before, count_after)

    def test_extract_date(self):
        with app.test_request_context():
            self.assertIsNone(extract_date('fake_name'))
        with app.test_request_context('/?from_date=2015-02-24'):
            self.assertEqual(datetime(2015, 2, 24).date(),
                             extract_date('from_date'))
        with app.test_request_context('/?from_date=20150224'):
            self.assertRaises(DateExtractionError, extract_date,
                              'from_date')

    def test_get_from_date(self):
        with app.test_request_context():
            expected = datetime.utcnow().date() - \
                timedelta(days=app.config['CSV_DEFAULT_FROM_DATE_DAYS'])
            actual = get_from_date()
            self.assertEqual(expected, actual)

        with app.test_request_context('/?from_date=2015-02-24'):
            expected = datetime(2015, 2, 24).date()
            actual = get_from_date()
            self.assertEqual(expected, actual)

    def test_to_date(self):
        with app.test_request_context():
            actual = get_to_date()
            self.assertEqual(datetime.utcnow().date(), actual)

        with app.test_request_context('/?to_date=2015-02-25'):
            expected = datetime(2015, 2, 25).date()
            actual = get_to_date()
            self.assertEqual(expected, actual)

    def test_get_oswls_query_with_dates(self):
        num = 20
        for resource_type in self.RESOURCE_TYPES:
            # Fetching oswls count
            count_before = get_oswls_query(resource_type, None, None).count()

            # Generating oswls without installation info
            oswls = self.get_saved_oswls(num, resource_type)
            self.get_saved_inst_structs(oswls)

            # Checking count of fetched oswls
            count_after = get_oswls_query(
                resource_type, None, None).count()
            self.assertEqual(num + count_before, count_after)
            count_after = get_oswls_query(
                resource_type, None, datetime.utcnow().date()).count()
            self.assertEqual(num + count_before, count_after)
            count_after = get_oswls_query(
                resource_type,
                datetime.utcnow().date() - timedelta(days=100),
                datetime.utcnow().date()).count()
            self.assertEqual(num + count_before, count_after)
            count_after = get_oswls_query(
                resource_type,
                datetime.utcnow().date(),
                datetime.utcnow().date() - timedelta(days=100)).count()
            self.assertEqual(0, count_after)

    def test_get_inst_structures_query(self):
        # Fetching inst structures count
        count_before = get_inst_structures_query().count()

        oswls = self.get_saved_oswls(200, consts.OSWL_RESOURCE_TYPES.vm)
        inst_structures = self.get_saved_inst_structs(oswls)
        num = len(inst_structures)

        # Checking count of fetched inst structures
        count_after = get_inst_structures_query(None, None).count()
        self.assertEqual(num + count_before, count_after)
        count_after = get_inst_structures_query(
            None, datetime.utcnow().date()).count()
        self.assertEqual(num + count_before, count_after)
        count_after = get_inst_structures_query(
            datetime.utcnow().date() - timedelta(days=100),
            datetime.utcnow().date()).count()
        self.assertEqual(num + count_before, count_after)
        count_after = get_inst_structures_query(
            datetime.utcnow().date(),
            datetime.utcnow().date() - timedelta(days=100)).count()
        self.assertEqual(0, count_after)

    def test_get_inst_structures_query_not_returns_filtered(self):
        # Fetching inst structures count
        count_initial = get_inst_structures_query().count()

        # Generating filtered inst structures
        oswls = self.get_saved_oswls(10, consts.OSWL_RESOURCE_TYPES.vm,
                                     stats_per_mn_range=(1, 1))
        self.get_saved_inst_structs(oswls, is_filtered_values=(True,))

        # Checking filtered inst structures don't fetched
        count_with_filtered = get_inst_structures_query(None, None).count()
        self.assertEquals(count_initial, count_with_filtered)

        # Generating not filtered inst structures
        oswls = self.get_saved_oswls(20, consts.OSWL_RESOURCE_TYPES.vm,
                                     stats_per_mn_range=(1, 1))
        inst_structures = self.get_saved_inst_structs(
            oswls, is_filtered_values=(None, False))
        not_filtered_num = len(inst_structures)

        # Checking not filtered inst structures fetched
        count_with_not_filtered = get_inst_structures_query(None, None).count()
        get_inst_structures_query(None, None).all()
        self.assertEquals(count_initial + not_filtered_num,
                          count_with_not_filtered)

    def test_no_filtered_structures(self):
        oswls = self.get_saved_oswls(100, consts.OSWL_RESOURCE_TYPES.vm,
                                     stats_per_mn_range=(1, 1))
        self.get_saved_inst_structs(
            oswls, is_filtered_values=(True, False, None))
        with app.test_request_context():
            for inst_structure in get_inst_structures():
                self.assertNotEqual(True, inst_structure.is_filtered)

    def test_get_resources_types(self):
        for resource_type in self.RESOURCE_TYPES:
            self.get_saved_oswls(1, resource_type)
        resources_names = get_resources_types()
        self.assertItemsEqual(self.RESOURCE_TYPES, resources_names)

    def test_get_all_reports(self):
        oswls = []
        for resource_type in self.RESOURCE_TYPES:
            oswls.extend(self.get_saved_oswls(10, resource_type))
        self.get_saved_inst_structs(oswls)

        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=30)
        reports = ce.get_all_reports(from_date, to_date, {})

        expected_reports = [
            ce.CLUSTERS_REPORT_FILE,
            ce.PLUGINS_REPORT_FILE
        ]
        for resource_type in self.RESOURCE_TYPES:
            expected_reports.append('{}.csv'.format(resource_type))

        actual_reports = [name for _, name in reports]
        self.assertItemsEqual(expected_reports, actual_reports)

    def test_get_all_reports_with_future_dates(self):
        oswls = []
        for resource_type in self.RESOURCE_TYPES:
            oswls.extend(self.get_saved_oswls(10, resource_type))
        self.get_saved_inst_structs(oswls)

        from_date = datetime.utcnow()
        to_date = from_date + timedelta(days=7)

        reports_generators = ce.get_all_reports(from_date, to_date, {})

        # Checking no exception raised
        for report_generator, report_name in reports_generators:
            for _ in report_generator:
                pass

    def test_get_action_logs(self):
        action_name = StatsToCsv.NETWORK_VERIFICATION_ACTION
        action_logs = [
            ActionLog(
                master_node_uid='ids_order',
                external_id=200,
                body={'cluster_id': 1,
                      'end_timestamp': datetime.utcnow().isoformat(),
                      'action_type': 'nailgun_task',
                      'action_name': action_name,
                      'additional_info': {'ended_with_status': 'error'}}
            ),
            ActionLog(
                master_node_uid='ids_order',
                external_id=1,
                body={'cluster_id': 1,
                      'end_timestamp': datetime.utcnow().isoformat(),
                      'action_type': 'nailgun_task',
                      'action_name': action_name,
                      'additional_info': {'ended_with_status': 'ready'}}
            ),
            ActionLog(
                master_node_uid='normal',
                external_id=200,
                body={'cluster_id': 1,
                      'end_timestamp': datetime.utcnow().isoformat(),
                      'action_type': 'nailgun_task',
                      'action_name': action_name,
                      'additional_info': {'ended_with_status': 'ready'}}
            ),
            ActionLog(
                master_node_uid='yesterday',
                external_id=1,
                body={'cluster_id': 1,
                      'end_timestamp': (datetime.utcnow() -
                                        timedelta(days=-1)).isoformat(),
                      'action_type': 'nailgun_task',
                      'action_name': action_name,
                      'additional_info': {'ended_with_status': 'ready'}}
            ),
            ActionLog(
                master_node_uid='wrong_name',
                external_id=1,
                body={'cluster_id': 1,
                      'end_timestamp': (datetime.utcnow() -
                                        timedelta(days=-1)).isoformat(),
                      'action_type': 'nailgun_task',
                      'action_name': 'fake_name',
                      'additional_info': {'ended_with_status': 'ready'}}
            ),
            ActionLog(
                master_node_uid='no_end_ts',
                external_id=1,
                body={'cluster_id': 1, 'action_type': 'nailgun_task',
                      'action_name': action_name,
                      'additional_info': {'ended_with_status': 'ready'}}
            ),
        ]
        for action_log in action_logs:
            db.session.add(action_log)
        db.session.commit()
        to_date = from_date = datetime.utcnow().date().strftime('%Y-%m-%d')

        req_params = '/?from_date={0}&to_date={1}'.format(from_date, to_date)
        with app.test_request_context(req_params):
            action_logs = list(get_action_logs())

        # Checking no old and no_end_ts action logs
        for action_log in action_logs:
            al = ActionLogInfo(*action_log)
            self.assertNotIn(al.master_node_uid, ('no_end_ts', 'yesterday'))

        # Checking selected right action logs
        # self.assertEqual(2, len(action_logs))
        for action_log in action_logs:
            al = ActionLogInfo(*action_log)
            self.assertIn(al.master_node_uid, ('normal', 'ids_order'), al)

        # Checking last action log is selected
        for action_log in action_logs:
            al = ActionLogInfo(*action_log)
            self.assertEqual(200, al.external_id, al)
