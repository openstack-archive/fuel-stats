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

INSTALLATION_INFO_SKELETON = {
    'allocated_nodes_num': None,
    'clusters': [
        {
            'attributes': {
                'assign_public_to_all_nodes': None,
                'ceilometer': None,
                'debug_mode': None,
                'ephemeral_ceph': None,
                'heat': None,
                'images_ceph': None,
                'images_vcenter': None,
                'iser': None,
                'kernel_params': None,
                'libvirt_type': None,
                'mellanox': None,
                'mellanox_vf_num': None,
                'murano': None,
                'nsx': None,
                'nsx_replication': None,
                'nsx_transport': None,
                'objects_ceph': None,
                'osd_pool_size': None,
                'provision_method': None,
                'sahara': None,
                'syslog_transport': None,
                'use_cow_images': None,
                'vcenter': None,
                'vlan_splinters': None,
                'vlan_splinters_ovs': None,
                'volumes_ceph': None,
                'volumes_lvm': None,
                'volumes_vmdk': None
            },
            'fuel_version': None,
            'id': None,
            'is_customized': None,
            'mode': None,
            'net_provider': None,
            'node_groups': [{'id': None, 'nodes': [{}]}],
            'nodes': [
                {
                    'bond_interfaces': [
                        {'id': None, 'slaves': [{}]}
                    ],
                    'error_type': None,
                    'group_id': None,
                    'id': None,
                    'manufacturer': None,
                    'nic_interfaces': [{'id': None}],
                    'online': None,
                    'os': None,
                    'pending_addition': None,
                    'pending_deletion': None,
                    'pending_roles': [{}],
                    'platform_name': None,
                    'roles': [{}],
                    'status': None
                }
            ],
            'nodes_num': None,
            'openstack_info': {
                'images': [{'size': None, 'unit': None}],
                'nova_servers_count': None
            },
            'release': {'name': None, 'os': None, 'version': None},
            'status': None
        }
    ],
    'clusters_num': None,
    'creation_date': None,
    'fuel_release': {
        'api': None,
        'astute_sha': None,
        'build_id': None,
        'build_number': None,
        'feature_groups': [{}],
        'fuellib_sha': None,
        'fuelmain_sha': None,
        'nailgun_sha': None,
        'ostf_sha': None,
        'production': None,
        'release': None
    },
    'master_node_uid': None,
    'modification_date': None,
    'unallocated_nodes_num': None,
    'user_information': {
        'company': None,
        'contact_info_provided': None,
        'email': None,
        'name': None
    }
}
