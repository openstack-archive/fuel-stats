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

from fuel_analytics.api.common import consts

INSTALLATION_INFO_SKELETON = {
    'structure': {
        'allocated_nodes_num': None,
        'clusters': [
            {
                'attributes': {
                    'assign_public_to_all_nodes': None,
                    'auto_assign_floating_ip': None,
                    'ceilometer': None,
                    'corosync_verified': None,
                    'debug_mode': None,
                    'ephemeral_ceph': None,
                    'external_mongo_replset': None,
                    'external_ntp_list': None,
                    'heat': None,
                    'images_ceph': None,
                    'images_vcenter': None,
                    'ironic': None,
                    'iser': None,
                    'kernel_params': None,
                    'libvirt_type': None,
                    'mellanox': None,
                    'mellanox_vf_num': None,
                    'mongo': None,
                    'murano': None,
                    'murano-cfapi': None,
                    'murano_glance_artifacts_plugin': None,
                    'neutron_dvr': None,
                    'neutron_l2_pop': None,
                    'neutron_l3_ha': None,
                    'nova_quota': None,
                    'nsx': None,
                    'nsx_replication': None,
                    'nsx_transport': None,
                    'objects_ceph': None,
                    'osd_pool_size': None,
                    'provision_method': None,
                    'public_ssl_cert_source': None,
                    'public_ssl_horizon': None,
                    'public_ssl_services': None,
                    'puppet_debug': None,
                    'repos': None,
                    'resume_guests_state_on_host_boot': None,
                    'sahara': None,
                    'syslog_transport': None,
                    'task_deploy': None,
                    'use_cow_images': None,
                    'volumes_block_device': None,
                    'vcenter': None,
                    'vlan_splinters': None,
                    'vlan_splinters_ovs': None,
                    'volumes_ceph': None,
                    'volumes_lvm': None,
                    'volumes_vmdk': None,
                    'workloads_collector_enabled': None,
                },
                'vmware_attributes': {
                    'vmware_az_cinder_enable': None,
                    'vmware_az_nova_computes_num': None
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
                'network_configuration': {
                    'segmentation_type': None,
                    'net_l23_provider': None,
                    'net_manager': None,
                    'fixed_networks_vlan_start': None,
                    'fixed_network_size': None,
                    'fixed_networks_amount': None
                },
                'installed_plugins': [
                    {
                        'name': None,
                        'version': None,
                        'releases': [{
                            'deployment_scripts_path': None,
                            'repository_path': None,
                            'mode': [],
                            'os': None,
                            'version': None,
                        }],
                        'fuel_version': None,
                        'package_version': None,
                    }
                ],
                'release': {'name': None, 'os': None, 'version': None},
                'status': None
            }
        ],
        'clusters_num': None,
        'fuel_release': {
            'api': None,
            'astute_sha': None,
            'build_id': None,
            'build_number': None,
            'feature_groups': [{}],
            'fuellib_sha': None,
            'fuel-library_sha': None,
            'fuelmain_sha': None,
            'nailgun_sha': None,
            'ostf_sha': None,
            'fuel-ostf_sha': None,
            'python-fuelclient_sha': None,
            'production': None,
            'release': None
        },
        'fuel_packages': [],
        'unallocated_nodes_num': None,
        'user_information': {
            'company': None,
            'contact_info_provided': None,
            'email': None,
            'name': None
        }
    },
    'master_node_uid': None,
    'modification_date': None,
    'creation_date': None
}

OSWL_SKELETONS = {
    'general': {
        'master_node_uid': None,
        'cluster_id': None,
        'stats_on_date': None,
        'resource_type': None,
        'version_info': {
            'fuel_release': None,
            'release_version': None,
            'release_os': None,
            'release_name': None,
            'environment_version': None
        }
    },
    consts.OSWL_RESOURCE_TYPES.vm: {
        'id': None,
        'status': None,
        'tenant_id': None,
        'host_id': None,
        'created_at': None,
        'power_state': None,
        'flavor_id': None,
        'image_id': None
    },
    consts.OSWL_RESOURCE_TYPES.flavor: {
        'id': None,
        'ram': None,
        'vcpus': None,
        'ephemeral': None,
        'disk': None,
        'swap': None,
    },
    consts.OSWL_RESOURCE_TYPES.volume: {
        'id': None,
        'availability_zone': None,
        'encrypted_flag': None,
        'bootable_flag': None,
        'status': None,
        'volume_type': None,
        'size': None,
        'snapshot_id': None,
        'tenant_id': None
    },
    'volume_attachment': {
        "device": None,
        "server_id": None,
        "id": None
    },
    consts.OSWL_RESOURCE_TYPES.image: {
        'id': None,
        'minDisk': None,
        'minRam': None,
        'sizeBytes': None,
        'created_at': None,
        'updated_at': None,
    },
    consts.OSWL_RESOURCE_TYPES.tenant: {
        'id': None,
        'enabled_flag': None,
    },
    consts.OSWL_RESOURCE_TYPES.keystone_user: {
        'id': None,
        'enabled_flag': None,
        'tenant_id': None
    }
}
