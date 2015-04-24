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
import uuid

from fuel_analytics.test.base import BaseTest

from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import ActionLog
from fuel_analytics.api.db.model import InstallationStructure


class InstStructureTest(BaseTest):

    def gen_id(self, id_range=(0, 1000000)):
        return random.randint(*id_range)

    def generate_node(
            self,
            roles_range=(0, 5),
            node_roles=('compute', 'controller', 'cinder', 'ceph-osd',
                        'zabbix', 'mongo'),
            oses=('Ubuntu', 'CentOs', 'Ubuntu LTS XX'),
            node_statuses = ('ready', 'discover', 'provisioning',
                             'provisioned', 'deploying', 'error'),
            manufacturers = ('Dell Inc.', 'VirtualBox', 'QEMU',
                             'VirtualBox', 'Supermicro', 'Cisco Systems Inc',
                             'KVM', 'VMWARE', 'HP')
    ):
        roles = []
        for _ in xrange(random.randint(*roles_range)):
            roles.append(random.choice(node_roles))
        node = {
            'id': self.gen_id(),
            'roles': roles,
            'os': random.choice(oses),
            'status': random.choice(node_statuses),
            'manufacturer': random.choice(manufacturers)
        }
        return node

    def generate_cluster(
            self,
            nodes_range=(0, 100),
            oses=('Ubuntu', 'CentOs', 'Ubuntu LTS XX'),
            release_names=('Juno on CentOS 6.5', 'Juno on Ubuntu 12.04.4'),
            release_versions=('6.0 TechPreview', '6.0 GA', '6.1'),
            cluster_statuses=('new', 'deployment', 'stopped', 'operational',
                              'error', 'remove', 'update', 'update_error'),
            libvirt_names=('qemu', 'kvm', 'vCenter'),
            plugins_num_range=(0, 5)
    ):
        nodes_num = random.randint(*nodes_range)
        cluster = {
            'id': self.gen_id(),
            'nodes_num': nodes_num,
            'release': {
                'os': random.choice(oses),
                'name': random.choice(release_names),
                'version': random.choice(release_versions),
            },
            'status': random.choice(cluster_statuses),
            'nodes': [],
            'attributes': {
                'libvirt_type': random.choice(libvirt_names),
                'heat': random.choice((True, False)),
            },
            'vmware_attributes': {
                'vmware_az_cinder_enable': [True, False],
            }
        }
        network_configuration = self.generate_network_configuration()
        cluster.update(network_configuration)
        cluster['installed_plugins'] = self.generate_installed_plugins(
            plugins_num_range=plugins_num_range)
        for _ in six.moves.range(nodes_num):
            cluster['nodes'].append(self.generate_node())
        return cluster

    def generate_network_configuration(self):
        return random.choice((
            {'network_configuration': {
                'segmentation_type': random.choice(("gre", "vlan")),
                'net_l23_provider': random.choice(("ovs", "nsx")),
            }},
            {'network_configuration': {
                'net_manager': random.choice(('FlatDHCPManager',
                                              'VlanManager')),
                'fixed_networks_vlan_start': random.choice((2, 3, None)),
                'fixed_network_size': random.randint(0, 255),
                'fixed_networks_amount': random.randint(0, 10),
            }},
            {'network_configuration': {}},
            {}
        ))

    def generate_installed_plugins(
            self,
            plugins_num_range=(0, 5),
            plugins_names=('fuel-plugin-gluster-fs', 'fuel-plugin-vpnaas')
    ):
        plugins_info = []
        for i in six.moves.range(random.randint(*plugins_num_range)):
            plugins_info.append({
                'id': i,
                'name': random.choice(plugins_names)
            })
        return plugins_info

    def _fuel_release_gen(self, releases):
        return {
            'release': random.choice(releases),
            'api': 1,
            'nailgun_sha': "Unknown build nailgun",
            'astute_sha': "Unknown build astute",
            'fuellib_sha': "Unknown build fuellib",
            'ostf_sha': "Unknown build ostf",
            'fuelmain_sha': "Unknown build fuelmain",
            'feature_groups': ['experimental', 'mirantis']
        }

    def _fuel_release_gen_2015_04(self, releases):
        return {
            'release': random.choice(releases),
            'api': 1,
            'nailgun_sha': "Unknown build nailgun",
            'astute_sha': "Unknown build astute astute",
            'fuel-ostf_sha': "Unknown build fuel-ostf",
            'python-fuelclient_sha': "Unknown build python-fuelclient",
            'fuel-library_sha': "Unknown build fuel-library",
            'fuelmain_sha': "Unknown build fuelmain",
            'feature_groups': ['experimental', 'mirantis']
        }

    def generate_structure(self, clusters_num_range=(0, 10),
                           unallocated_nodes_num_range=(0, 20),
                           plugins_num_range=(0, 5),
                           release_generators=('_fuel_release_gen',
                                               '_fuel_release_gen_2015_04'),
                           releases=("6.0-techpreview", "6.0-ga")):
        clusters_num = random.randint(*clusters_num_range)

        release_generator = random.choice(release_generators)
        fuel_release = getattr(self, release_generator)(releases)

        structure = {
            'fuel_release': fuel_release,
            'clusters_num': clusters_num,
            'clusters': [],
            'unallocated_nodes_num_range': random.randint(
                *unallocated_nodes_num_range),
            'allocated_nodes_num': 0
        }

        for _ in xrange(clusters_num):
            cluster = self.generate_cluster(
                plugins_num_range=plugins_num_range)
            structure['clusters'].append(cluster)
            structure['allocated_nodes_num'] += cluster['nodes_num']
        return structure

    def generate_inst_structures(
            self, installations_num=100, creation_date_range=(1, 10),
            modification_date_range=(1, 10), clusters_num_range=(0, 10),
            plugins_num_range=(0, 5), releases=("6.0-techpreview", "6.0-ga"),
            release_generators=('_fuel_release_gen',
                                '_fuel_release_gen_2015_04')):
        for _ in xrange(installations_num):
            mn_uid = '{}'.format(uuid.uuid4())
            structure = self.generate_structure(
                clusters_num_range=clusters_num_range,
                plugins_num_range=plugins_num_range,
                releases=releases,
                release_generators=release_generators)
            creation_date = datetime.utcnow() - timedelta(
                days=random.randint(*creation_date_range))
            modification_date = datetime.utcnow() - timedelta(
                days=random.randint(*modification_date_range))
            obj = InstallationStructure(
                master_node_uid=mn_uid,
                structure=structure,
                creation_date=creation_date,
                modification_date=modification_date
            )
            yield obj

    def _get_saved_objs(self, generator_func, *args, **kwargs):
        objs = generator_func(*args, **kwargs)
        result = []
        for obj in objs:
            db.session.add(obj)
            result.append(obj)
        db.session.commit()
        return result

    def get_saved_inst_structures(self, *args, **kwargs):
        return self._get_saved_objs(self.generate_inst_structures,
                                    *args, **kwargs)

    def generate_action_logs(
            self, inst_sturctures, num_per_struct_range=(1, 100),
            action_types=('nailgun_task',),
            action_groups=('cluster_changes', 'cluster_checking',
                           'operations'),
            action_names=('deploy', 'deployment', 'provision',
                          'stop_deployment', 'reset_environment',
                          'update', 'node_deletion', 'cluster_deletion',
                          'check_before_deployment', 'check_networks',
                          'verify_networks')):
        for struct in inst_sturctures:
            for idx in six.moves.range(random.randint(*num_per_struct_range)):
                action_type = random.choice(action_types)
                action_name = random.choice(action_names)
                body = {
                    "id": idx,
                    "actor_id": six.text_type(uuid.uuid4()),
                    "action_group": random.choice(action_groups),
                    "action_name": random.choice(action_names),
                    "action_type": action_type,
                    "start_timestamp": datetime.utcnow().isoformat(),
                    "end_timestamp": datetime.utcnow().isoformat(),
                    "additional_info": {
                        "parent_task_id": None,
                        "subtasks_ids": [],
                        "operation": action_name
                    },
                    "is_sent": False,
                    "cluster_id": idx
                }
                obj = ActionLog(
                    master_node_uid=struct.master_node_uid,
                    external_id=idx,
                    body=body
                )
                yield obj

    def get_saved_action_logs(self, *args, **kwargs):
        return self._get_saved_objs(self.generate_action_logs,
                                    *args, **kwargs)
