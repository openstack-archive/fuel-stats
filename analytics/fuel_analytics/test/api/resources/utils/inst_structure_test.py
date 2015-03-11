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
            segmentation_types=('vlan', 'gre')
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
            }
        }
        network_configuration = self.generate_network_configuration()
        cluster.update(network_configuration)
        cluster['installed_plugins'] = self.generate_installed_plugins()
        for _ in six.moves.range(nodes_num):
            cluster['nodes'].append(self.generate_node())
        return cluster

    def generate_network_configuration(self):
        return random.choice((
            {'network_configuration': {
                'segmentation_type': random.choice(("gre", "vlan")),
                'net_l23_provider': random.choice(("ovw", "nsx")),
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

    def generate_structure(self, clusters_num_range=(0, 10),
                           unallocated_nodes_num_range=(0, 20)):
        clusters_num = random.randint(*clusters_num_range)
        fuel_release = {
            'release': random.choice(("6.0-techpreview", "6.0-ga")),
            'api': 1,
            'nailgun_sha': "Unknown build",
            'astute_sha': "Unknown build",
            'fuellib_sha': "Unknown build",
            'ostf_sha': "Unknown build",
            'feature_groups': ['experimental', 'mirantis']
        }

        structure = {
            'fuel_release': fuel_release,
            'clusters_num': clusters_num,
            'clusters': [],
            'unallocated_nodes_num_range': random.randint(
                *unallocated_nodes_num_range),
            'allocated_nodes_num': 0
        }

        for _ in xrange(clusters_num):
            cluster = self.generate_cluster()
            structure['clusters'].append(cluster)
            structure['allocated_nodes_num'] += cluster['nodes_num']
        return structure

    def generate_inst_structures(self, installations_num=100,
                                 creation_date_range=(1, 10),
                                 modification_date_range=(1, 10)):
        for _ in xrange(installations_num):
            mn_uid = '{}'.format(uuid.uuid4())
            structure = self.generate_structure()
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

    def get_saved_inst_structures(self, *args, **kwargs):
        inst_structs = self.generate_inst_structures(*args, **kwargs)
        result = []
        for inst_struct in inst_structs:
            db.session.add(inst_struct)
            result.append(inst_struct)
        db.session.commit()
        return result
