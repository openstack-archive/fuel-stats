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
from datetime import timedelta
import random
import six
import uuid

from fuel_analytics.test.base import BaseTest

from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
from fuel_analytics.api.db.model import OpenStackWorkloadStats
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
import types


class OswlStatsToCsvTest(BaseTest):

    def generate_vms(self, vms_num, statuses=('on', 'off'),
                     created_at_range=(1, 10),
                     power_states_range=(1, 10)):
        result = []
        for i in xrange(vms_num):
            result.append({
                'id': i,
                'status': random.choice(statuses),
                'tenant_id': 'tenant_id_{}'.format(i),
                'host_id': 'host_id_{}'.format(i),
                'created_at': (datetime.utcnow() - timedelta(
                    days=random.randint(*created_at_range))).isoformat(),
                'power_state': random.randint(*power_states_range),
                'flavor_id': 'flavor_id_{}'.format(i),
                'image_id': 'image_id_{}'.format(i),
            })
        return result

    def generate_removed_vms(self, vms_num):
        result = {}
        for vm in self.generate_vms(vms_num):
            vm['time'] = datetime.utcnow().time().isoformat()
            result[vm['id']] = vm
        return result

    def generate_added_vms(self, vms_num):
        result = {}
        for i in xrange(vms_num):
            result[i] = {'time': datetime.utcnow().time().isoformat()}
        return result

    def generate_modified_vms(self, vms_num, modifs_num_range=(0, 3),
                              power_states_range=(1, 10)):
        result = {}
        for i in xrange(vms_num):
            for _ in xrange(random.randint(*modifs_num_range)):
                result.setdefault(i, []).append({
                    'time': datetime.utcnow().time().isoformat(),
                    'power_state': random.choice(power_states_range)
                })
        return result

    def generate_vm_oswls(self, oswl_num, current_vms_num_range=(0, 7),
                          created_date_range=(1, 10),
                          added_vms_num_range=(0, 5),
                          removed_vms_num_range=(0, 3),
                          modified_vms_num_range=(0, 15),
                          stats_per_mn_range=(1, 10),
                          cluster_ids_range=(1, 5)):
        i = 1
        current_mn_stats = 0
        while i <= oswl_num:
            if not current_mn_stats:
                mn_uid = six.text_type(uuid.uuid4())
                current_mn_stats = random.randint(*stats_per_mn_range)

            if current_mn_stats:
                i += 1
                created_date = (datetime.utcnow() - timedelta(
                    days=random.randint(*created_date_range))).\
                    date().isoformat()
                obj = OpenStackWorkloadStats(
                    master_node_uid=mn_uid,
                    external_id=i,
                    cluster_id=random.choice(cluster_ids_range),
                    created_date=created_date,
                    updated_time=datetime.utcnow().time().isoformat(),
                    resource_type=consts.OSWL_RESOURCE_TYPES.vm,
                    resource_checksum=six.text_type(uuid.uuid4()),
                    resource_data={
                        'current': self.generate_vms(
                            random.randint(*current_vms_num_range)),
                        'added': self.generate_added_vms(
                            random.randint(*added_vms_num_range)),
                        'modified': self.generate_modified_vms(
                            random.randint(*modified_vms_num_range)),
                        'removed': self.generate_removed_vms(
                            random.randint(*removed_vms_num_range))
                    }
                )
                current_mn_stats -= 1
            yield obj

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
