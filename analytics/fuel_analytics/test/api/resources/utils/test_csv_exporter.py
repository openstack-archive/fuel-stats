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
from flask import request
import itertools
import mock
import os
import shutil
import tempfile
import zipfile

from fuel_analytics.test.api.resources.utils.oswl_test import OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.common import consts
from fuel_analytics.api.errors import DateExtractionError
from fuel_analytics.api.resources.csv_exporter import archive_dir
from fuel_analytics.api.resources.csv_exporter import extract_date
from fuel_analytics.api.resources.csv_exporter import get_from_date
from fuel_analytics.api.resources.csv_exporter import get_inst_structures_query
from fuel_analytics.api.resources.csv_exporter import get_oswls_query
from fuel_analytics.api.resources.csv_exporter import get_resources_types
from fuel_analytics.api.resources.csv_exporter import get_to_date
from fuel_analytics.api.resources.csv_exporter import save_all_reports


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
            with mock.patch.object(request, 'args', {}):
                self.assertIsNone(extract_date('fake_name'))
            with mock.patch.object(request, 'args',
                                   {'from_date': '2015-02-24'}):
                self.assertEqual(datetime(2015, 2, 24).date(),
                                 extract_date('from_date'))
            with mock.patch.object(request, 'args',
                                   {'from_date': '20150224'}):
                self.assertRaises(DateExtractionError, extract_date,
                                  'from_date')

    def test_get_from_date(self):
        with app.test_request_context():
            with mock.patch.object(request, 'args', {}):
                expected = datetime.utcnow().date() - \
                    timedelta(days=app.config['CSV_DEFAULT_FROM_DATE_DAYS'])
                actual = get_from_date()
                self.assertEqual(expected, actual)
            with mock.patch.object(request, 'args',
                                   {'from_date': '2015-02-24'}):
                expected = datetime(2015, 2, 24).date()
                actual = get_from_date()
                self.assertEqual(expected, actual)

    def test_to_date(self):
        with app.test_request_context():
            with mock.patch.object(request, 'args', {}):
                actual = get_to_date()
                self.assertEqual(datetime.utcnow().date(), actual)
            with mock.patch.object(request, 'args',
                                   {'to_date': '2015-02-25'}):
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

    def test_get_resources_types(self):
        for resource_type in self.RESOURCE_TYPES:
            self.get_saved_oswls(1, resource_type)
        resources_names = get_resources_types()
        self.assertItemsEqual(self.RESOURCE_TYPES, resources_names)

    def test_save_all_reports(self):
        oswls = []
        for resource_type in self.RESOURCE_TYPES:
            oswls.extend(self.get_saved_oswls(10, resource_type))
        self.get_saved_inst_structs(oswls)
        tmp_dir = tempfile.mkdtemp()
        try:
            with app.test_request_context():
                save_all_reports(tmp_dir)
            files = itertools.chain(('clusters', ), self.RESOURCE_TYPES)
            for f in files:
                path = os.path.join(tmp_dir, '{}.csv'.format(f))
                self.assertTrue(os.path.isfile(path), path)
        finally:
            shutil.rmtree(tmp_dir)

    def test_archive_dir(self):
        oswls = []
        for resource_type in self.RESOURCE_TYPES:
            oswls.extend(self.get_saved_oswls(10, resource_type))
        self.get_saved_inst_structs(oswls)
        tmp_dir = tempfile.mkdtemp()
        try:
            with app.test_request_context():
                save_all_reports(tmp_dir)
            files = itertools.chain(('clusters', ), self.RESOURCE_TYPES)
            for f in files:
                path = os.path.join(tmp_dir, '{}.csv'.format(f))
                self.assertTrue(os.path.isfile(path), path)
            archive = archive_dir(tmp_dir)
            try:
                self.assertTrue(zipfile.is_zipfile(archive.filename))
            finally:
                os.unlink(archive.filename)
        finally:
            shutil.rmtree(tmp_dir)
