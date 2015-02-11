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
import functools
from fuel_analytics.api.common import consts
import six

from fuel_analytics.test.api.resources.utils.oswl_test import OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import db
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
import types


class OswlStatsToCsvTest(OswlTest, DbTest):

    def test_get_vm_keys_paths(self):
        exporter = OswlStatsToCsv()
        oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
            exporter.get_vm_keys_paths()
        self.assertTrue(['external_id'] in oswl_keys_paths)
        self.assertTrue(['vm', 'id'] in vm_keys_paths)
        self.assertTrue(['vm', 'is_added'] in csv_keys_paths)
        self.assertTrue(['vm', 'is_modified'] in csv_keys_paths)
        self.assertTrue(['vm', 'is_removed'] in csv_keys_paths)

    def test_get_flatten_vms(self):
        exporter = OswlStatsToCsv()
        oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
            exporter.get_vm_keys_paths()
        oswls = self.generate_vm_oswls(2)
        flatten_vms = exporter.get_flatten_vms(oswl_keys_paths, vm_keys_paths,
                                               oswls)
        self.assertTrue(isinstance(flatten_vms, types.GeneratorType))
        for _ in flatten_vms:
            pass

    def test_get_additional_vm_info(self):
        exporter = OswlStatsToCsv()
        added_num = 0
        modified_num = 3
        removed_num = 5
        oswls = self.generate_vm_oswls(
            1,
            added_vms_num_range=(added_num, added_num),
            modified_vms_num_range=(modified_num, modified_num),
            removed_vms_num_range=(removed_num, removed_num)
        )
        oswl = oswls.next()

        # Saving data for true JSON loading from DB object
        db.session.add(oswl)
        db.session.commit()

        resource_data = oswl.resource_data
        for vm in resource_data['current']:
            # After conversion into JSON dict keys became strings
            vm_id = six.text_type(vm['id'])
            expected = [
                vm_id in resource_data['added'],
                vm_id in resource_data['modified'],
                vm_id in resource_data['removed'],
                ]
            self.assertListEqual(expected,
                                 exporter.get_additional_vm_info(vm, oswl))

        # Cleaning DB
        db.session.delete(oswl)
        db.session.commit()

    def test_export_vms(self):
        exporter = OswlStatsToCsv()
        oswls = self.generate_vm_oswls(200)
        result = exporter.export_vms(oswls)
        self.assertTrue(isinstance(result, types.GeneratorType))
        output = six.StringIO(list(result))
        reader = csv.reader(output)
        for _ in reader:
            pass

    def test_export(self):
        exporter = OswlStatsToCsv()
        resource_types = (
            (consts.OSWL_RESOURCE_TYPES.vm,
             functools.partial(self.generate_vm_oswls, 200)),
        )
        for resource_type, gen_func in resource_types:
            result = exporter.export(resource_type)
        # self.assertTrue(isinstance(result, types.GeneratorType))
        # output = six.StringIO(list(result))
        # reader = csv.reader(output)
        # for _ in reader:
        #     pass
