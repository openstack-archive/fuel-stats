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

import csv
from datetime import datetime
import six
import types

from fuel_analytics.test.api.resources.utils.oswl_test import OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
from fuel_analytics.api.resources.csv_exporter import get_oswls
from fuel_analytics.api.resources.csv_exporter import get_oswls_query
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv


class OswlStatsToCsvTest(OswlTest, DbTest):

    RESOURCE_TYPES = (
        consts.OSWL_RESOURCE_TYPES.vm,
        consts.OSWL_RESOURCE_TYPES.flavor
    )

    def test_get_keys_paths(self):
        for resource_type in self.RESOURCE_TYPES:
            exporter = OswlStatsToCsv()
            oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
                exporter.get_resource_keys_paths(resource_type)
            self.assertFalse(['external_id'] in oswl_keys_paths)
            self.assertFalse(['updated_time'] in oswl_keys_paths)
            self.assertTrue([resource_type, 'id'] in resource_keys_paths)
            self.assertTrue([resource_type, 'is_added'] in csv_keys_paths)
            self.assertTrue([resource_type, 'is_modified'] in csv_keys_paths)
            self.assertTrue([resource_type, 'is_removed'] in csv_keys_paths)

    def test_get_flatten_resources(self):
        for resource_type in self.RESOURCE_TYPES:
            exporter = OswlStatsToCsv()
            oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
                exporter.get_resource_keys_paths(resource_type)
            oswls = self.generate_oswls(2, resource_type)
            flatten_vms = exporter.get_flatten_resources(
                resource_type, oswl_keys_paths, vm_keys_paths, oswls)
            self.assertTrue(isinstance(flatten_vms, types.GeneratorType))
            for _ in flatten_vms:
                pass

    def test_get_additional_info(self):
        exporter = OswlStatsToCsv()
        added_num = 0
        modified_num = 3
        removed_num = 5
        num = 1
        for resource_type in self.RESOURCE_TYPES:
            oswls = self.generate_oswls(
                num,
                resource_type,
                added_num_range=(added_num, added_num),
                modified_num_range=(modified_num, modified_num),
                removed_num_range=(removed_num, removed_num)
            )
            oswl = oswls.next()

            # Saving data for true JSON loading from DB object
            db.session.add(oswl)
            db.session.commit()
            resource_data = oswl.resource_data
            for resource in resource_data['current']:
                # After conversion into JSON dict keys became strings
                resource_id = six.text_type(resource['id'])
                expected = [
                    resource_id in resource_data['added'],
                    resource_id in resource_data['modified'],
                    resource_id in resource_data['removed'],
                ]
                actual = exporter.get_additional_resource_info(resource, oswl)
                self.assertListEqual(expected, actual)

    def test_export(self):
        exporter = OswlStatsToCsv()
        num = 200
        for resource_type in self.RESOURCE_TYPES:
            # Saving data for true JSON loading from DB object
            oswls_saved = self.get_saved_oswls(num, resource_type)
            # Saving installation structures for proper oswls filtering
            self.get_saved_inst_structs(oswls_saved)
            # Checking oswls filtered properly
            oswls = list(get_oswls(resource_type))
            self.assertEqual(num, len(oswls))
            # Checking export
            result = exporter.export(resource_type, oswls)
            self.assertTrue(isinstance(result, types.GeneratorType))
            output = six.StringIO(list(result))
            reader = csv.reader(output)
            for _ in reader:
                pass

    def test_export_on_empty_data(self):
        exporter = OswlStatsToCsv()
        for resource_type in self.RESOURCE_TYPES:
            result = exporter.export(resource_type, [])
            self.assertTrue(isinstance(result, types.GeneratorType))
            output = six.StringIO(list(result))
            reader = csv.reader(output)
            for _ in reader:
                pass

    def test_get_oswls_query(self):
        num = 2
        for resource_type in self.RESOURCE_TYPES[0:1]:
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

    def test_get_last_sync_date(self):
        exporter = OswlStatsToCsv()
        for resource_type in self.RESOURCE_TYPES:
            oswls_saved = self.get_saved_oswls(1, resource_type)
            inst_sturcts = self.get_saved_inst_structs(oswls_saved)
            inst_struct = inst_sturcts[0]
            inst_struct.modification_date = None
            db.session.commit()

            oswls = get_oswls(resource_type)
            oswl = oswls[0]
            self.assertEquals(
                inst_struct.creation_date,
                exporter.get_last_sync_date(oswl)
            )

            inst_struct.modification_date = datetime.utcnow()
            db.session.commit()
            oswls = get_oswls(resource_type)
            oswl = oswls[0]
            self.assertEquals(
                inst_struct.modification_date,
                exporter.get_last_sync_date(oswl)
            )

    def test_fill_date_gaps(self):
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.vm

        # # Generating vms time series for one master node
        # # vm without modification date
        # days = 5
        # oswls_saved = self.get_saved_oswls(1, resource_type, created_date_range=(days, days))
        # inst_sturcts = self.get_saved_inst_structs(oswls_saved, creation_date_range=(days, days))
        # inst_struct = inst_sturcts[0]
        # inst_struct.modification_date = None
        # db.session.commit()
        #
        # oswls = get_oswls(resource_type)
        # oswl = oswls[0]
        # self.assertIsNotNone(oswl.installation_created_date)
        # self.assertIsNone(oswl.installation_updated_date)
        #
        # # Checking only one record is present
        # oswls_seamless = exporter.fill_date_gaps(oswls)
        # self.assertEquals(1, len(list(oswls_seamless)))
        #
        # # Checking record is duplicated
        # inst_struct.modification_date = datetime.utcnow()
        # db.session.commit()
        #
        # oswls_seamless = exporter.fill_date_gaps(oswls)
        # self.assertEquals(days, len(list(oswls_seamless)))

    def test_fill_date_gaps_empty_data(self):
        exporter = OswlStatsToCsv()
        exporter.fill_date_gaps([])
