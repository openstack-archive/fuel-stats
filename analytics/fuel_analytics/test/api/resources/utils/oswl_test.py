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
import random
import six
from six.moves import range
import uuid

from fuel_analytics.test.base import BaseTest

from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
from fuel_analytics.api.db.model import InstallationStructure
from fuel_analytics.api.db.model import OpenStackWorkloadStats


class OswlTest(BaseTest):

    RESOURCE_TYPES = (
        consts.OSWL_RESOURCE_TYPES.vm,
        consts.OSWL_RESOURCE_TYPES.flavor,
        consts.OSWL_RESOURCE_TYPES.volume,
        consts.OSWL_RESOURCE_TYPES.image,
        consts.OSWL_RESOURCE_TYPES.tenant
    )

    RESOURCE_GENERATORS = {
        consts.OSWL_RESOURCE_TYPES.vm: ('generate_vms',
                                        'generate_modified_vms'),
        consts.OSWL_RESOURCE_TYPES.flavor: ('generate_flavors',
                                            'generate_modified_flavors'),
        consts.OSWL_RESOURCE_TYPES.volume: ('generate_volumes',
                                            'generate_modified_volumes'),
        consts.OSWL_RESOURCE_TYPES.image: ('generate_images',
                                           'generate_modified_images'),
        consts.OSWL_RESOURCE_TYPES.tenant: ('generate_tenants',
                                            'generate_modified_tenants'),
    }

    def generate_removed_resources(self, num, gen_func):
        result = []
        for vm in gen_func(num):
            vm['time'] = datetime.utcnow().time().isoformat()
            result.append(vm)
        return result

    def generate_added_resources(self, num):
        result = []
        for i in range(num):
            result.append({
                'id': i,
                'time': datetime.utcnow().time().isoformat()
            })
        return result

    def generate_vms(self, vms_num, statuses=('ACTIVE', 'ERROR', 'BUILT'),
                     created_at_range=(1, 10),
                     power_states_range=(1, 10)):
        result = []
        for i in range(vms_num):
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

    def generate_modified_vms(self, vms_num, modifs_num_range=(1, 10),
                              power_states_range=(1, 10)):
        result = []
        for i in range(vms_num):
            for _ in range(random.randint(*modifs_num_range)):
                result.append({
                    'id': i,
                    'time': datetime.utcnow().time().isoformat(),
                    'power_state': random.choice(power_states_range)
                })
        return result

    def generate_flavors(self, num, ram_range=(64, 24000),
                         vcpus_range=(1, 64), ephemeral_range=(1, 30),
                         disk_range=(1, 2048), swap_range=(1, 128)):
        result = []
        for i in range(num):
            result.append({
                'id': i,
                'ram': random.randint(*ram_range),
                'vcpus': random.randint(*vcpus_range),
                'ephemeral': random.randint(*ephemeral_range),
                'disk': random.randint(*disk_range),
                'swap': random.randint(*swap_range),
            })
        return result

    def generate_modified_flavors(self, num, modifs_num_range=(1, 3),
                                  swap_range=(1, 128),
                                  disk_range=(13, 23)):
        result = []
        for i in range(num):
            for _ in range(random.randint(*modifs_num_range)):
                result.append({
                    'id': i,
                    'time': datetime.utcnow().time().isoformat(),
                    'swap': random.randint(*swap_range),
                    'disk': random.randint(*disk_range)
                })
        return result

    def generate_volumes(self, num, avail_zones=('zone_0', 'zone_1', 'zone_2'),
                         statuses=('available', 'error'),
                         volume_types=('test_0', 'test_1'),
                         size_range=(1, 1024),
                         attachments=(None, 'att_0', 'att_1')
                         ):
        result = []
        for i in range(num):
            result.append({
                'id': i,
                'availability_zone': random.choice(avail_zones),
                'encrypted_flag': random.choice((False, True)),
                'bootable_flag': random.choice((False, True)),
                'status': random.choice(statuses),
                'volume_type': random.choice(volume_types),
                'size': random.randint(*size_range),
                'host': six.text_type(uuid.uuid4()),
                'snapshot_id': random.choice((
                    None, six.text_type(uuid.uuid4()))),
                'attachments': random.choice(attachments),
                'tenant_id': six.text_type(uuid.uuid4())
            })
        return result

    def generate_modified_volumes(self, num, modifs_num_range=(1, 3),
                                  size_range=(1, 1024),
                                  volume_types=('test_0', 'test_1')):
        result = []
        for i in range(num):
            for _ in range(random.randint(*modifs_num_range)):
                result.append({
                    'id': i,
                    'time': datetime.utcnow().time().isoformat(),
                    'size': random.randint(*size_range),
                    'volume_type': random.choice(volume_types)
                })
        return result

    def generate_images(self, num, min_disk_range=(1, 1024),
                        min_ram_range=(1, 2048), size_range=(1, 4096),
                        created_at_range=(1, 10), updated_at_range=(1, 10)):
        result = []
        for i in range(num):
            result.append({
                'id': i,
                'minDisk': random.randint(*min_disk_range),
                'minRam': random.randint(*min_ram_range),
                'sizeBytes': random.randint(*size_range),
                'created_at': (datetime.utcnow() - timedelta(
                    days=random.randint(*created_at_range))).isoformat(),
                'updated_at': (datetime.utcnow() - timedelta(
                    days=random.randint(*updated_at_range))).isoformat(),
            })
        return result

    def generate_modified_images(self, num, modifs_num_range=(1, 3),
                                 min_disk_range=(1, 1024),
                                 min_ram_range=(1, 4096),
                                 size_bytes_range=(1, 1024000)):
        result = []
        for i in range(num):
            for _ in range(random.randint(*modifs_num_range)):
                result.append({
                    'id': i,
                    'time': datetime.utcnow().time().isoformat(),
                    'minDisk': random.randint(*min_disk_range),
                    'minRam': random.randint(*min_ram_range),
                    'sizeBytes': random.randint(*size_bytes_range),
                })
        return result

    def generate_tenants(self, num, enabled_flag_values=(True, False)):
        result = []
        for i in range(num):
            result.append({
                'id': i,
                'enabled_flag': random.choice(enabled_flag_values)
            })
        return result

    def generate_modified_tenants(self, num, modifs_num_range=(1, 3),
                                  enabled_flag_values=(True, False)):
        result = []
        for i in range(num):
            for _ in range(random.randint(*modifs_num_range)):
                result.append({
                    'id': i,
                    'time': datetime.utcnow().time().isoformat(),
                    'enabled_flag': random.choice(enabled_flag_values)
                })
        return result

    def generate_oswls(self, oswl_num, resource_type,
                       current_num_range=(0, 7),
                       created_date_range=(1, 10),
                       added_num_range=(0, 5),
                       removed_num_range=(0, 3),
                       modified_num_range=(0, 15),
                       stats_per_mn_range=(1, 10),
                       cluster_ids_range=(1, 5)):
        i = 1
        current_mn_stats = 0
        gen_name, gen_modified_name = self.RESOURCE_GENERATORS[resource_type]
        gen = getattr(self, gen_name)
        gen_modified = getattr(self, gen_modified_name)
        while i <= oswl_num:
            if not current_mn_stats:
                mn_uid = six.text_type(uuid.uuid4())
                current_mn_stats = random.randint(*stats_per_mn_range)

            if current_mn_stats:
                i += 1
                created_date = (datetime.utcnow() - timedelta(
                    days=random.randint(*created_date_range))).\
                    date()
                obj = OpenStackWorkloadStats(
                    master_node_uid=mn_uid,
                    external_id=i,
                    cluster_id=random.choice(cluster_ids_range),
                    created_date=created_date,
                    updated_time=datetime.utcnow().time(),
                    resource_type=resource_type,
                    resource_checksum=six.text_type(uuid.uuid4()),
                    resource_data={
                        'current': gen(
                            random.randint(*current_num_range)),
                        'added': self.generate_added_resources(
                            random.randint(*added_num_range)),
                        'modified': gen_modified(
                            random.randint(*modified_num_range)),
                        'removed': self.generate_removed_resources(
                            random.randint(*removed_num_range),
                            gen)
                    }
                )
                current_mn_stats -= 1
            yield obj

    def get_saved_oswls(self, num, resource_type, *args, **kwargs):
        oswls = self.generate_oswls(num, resource_type, *args, **kwargs)
        result = []
        for oswl in oswls:
            db.session.add(oswl)
            result.append(oswl)
        db.session.commit()
        return result

    def generate_inst_structs(self, oswls,
                              creation_date_range=(2, 10),
                              modification_date_range=(2, 5),
                              is_modified_date_nullable=True):

        mn_uids = set()
        for oswl in oswls:
            if oswl.master_node_uid not in mn_uids:
                creation_date = (datetime.utcnow() - timedelta(
                    days=random.randint(*creation_date_range))).\
                    date().isoformat()
                if random.choice((False, is_modified_date_nullable)):
                    modification_date = None
                else:
                    modification_date = (datetime.utcnow() - timedelta(
                        days=random.randint(*modification_date_range))).\
                        date().isoformat()
                obj = InstallationStructure(
                    master_node_uid=oswl.master_node_uid,
                    creation_date=creation_date,
                    modification_date=modification_date,
                    structure={},
                )
                mn_uids.add(oswl.master_node_uid)
                yield obj

    def get_saved_inst_structs(self, oswls, *args, **kwargs):
        inst_structs = self.generate_inst_structs(oswls, *args, **kwargs)
        result = []
        for inst_struct in inst_structs:
            db.session.add(inst_struct)
            result.append(inst_struct)
        db.session.commit()
        return result
