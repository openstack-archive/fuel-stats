STRUCTURE_SKELETON = {
    "allocated_nodes_num": 2,
    "clusters": [
        {
            "attributes": {
                "assign_public_to_all_nodes": False,
                "ceilometer": False,
                "debug_mode": True,
                "ephemeral_ceph": False,
                "heat": True,
                "images_ceph": False,
                "images_vcenter": False,
                "iser": False,
                "kernel_params": "console=ttyS0,9600 console=tty0 rootdelay=90 nomodeset",
                "libvirt_type": "qemu",
                "mellanox": "disabled",
                "mellanox_vf_num": "16",
                "murano": False,
                "nsx": False,
                "nsx_replication": True,
                "nsx_transport": "stt",
                "objects_ceph": False,
                "osd_pool_size": "2",
                "provision_method": "cobbler",
                "sahara": False,
                "syslog_transport": "tcp",
                "use_cow_images": True,
                "vcenter": True,
                "volumes_ceph": False,
                "volumes_lvm": True,
                "volumes_vmdk": False
            },
            "fuel_version": "6.0",
            "id": 1,
            "is_customized": False,
            "mode": "multinode",
            "net_provider": "nova_network",
            "node_groups": [
                {
                    "id": 1,
                    "nodes": [
                        2,
                        1
                    ]
                }
            ],
            "nodes": [
                {
                    "bond_interfaces": [],
                    "error_type": None,
                    "group_id": 1,
                    "id": 1,
                    "manufacturer": "QEMU",
                    "nic_interfaces": [
                        {
                            "id": 5
                        },
                        {
                            "id": 4
                        },
                        {
                            "id": 3
                        },
                        {
                            "id": 2
                        },
                        {
                            "id": 1
                        }
                    ],
                    "online": True,
                    "os": "ubuntu",
                    "pending_addition": False,
                    "pending_deletion": False,
                    "pending_roles": [],
                    "platform_name": "Standard PC (i440FX + PIIX, 1996)",
                    "roles": [
                        "controller"
                    ],
                    "status": "ready"
                },
                {
                    "bond_interfaces": [],
                    "error_type": None,
                    "group_id": 1,
                    "id": 2,
                    "manufacturer": "QEMU",
                    "nic_interfaces": [
                        {
                            "id": 10
                        },
                        {
                            "id": 9
                        },
                        {
                            "id": 8
                        },
                        {
                            "id": 7
                        },
                        {
                            "id": 6
                        }
                    ],
                    "online": True,
                    "os": "ubuntu",
                    "pending_addition": False,
                    "pending_deletion": False,
                    "pending_roles": [],
                    "platform_name": "Standard PC (i440FX + PIIX, 1996)",
                    "roles": [
                        "compute"
                    ],
                    "status": "ready"
                }
            ],
            "nodes_num": 2,
            "openstack_info": {
                "nova_servers_count": 1
            },
            "release": {
                "name": "Juno on Ubuntu 12.04.4",
                "os": "Ubuntu",
                "version": "2014.2-6.0"
            },
            "status": "operational"
        }
    ],
    "clusters_num": 1,
    "fuel_release": {
        "api": "1.0",
        "astute_sha": "c15623d05ccdf7ac10873e7a90df954de8726280",
        "build_id": "2014-11-26_13-35-04",
        "build_number": "10",
        "feature_groups": [
            "mirantis"
        ],
        "fuellib_sha": "25eb629f3c6a6ff41cf187e260fe4ff456cfc4e4",
        "fuelmain_sha": "465afb6479a0b3c677040fb978cc109dcf62f774",
        "nailgun_sha": "bf9ddb9f9d5dbb09c4b50201ce176635791d7d3e",
        "ostf_sha": "a35f516f1606b0d03d51ff63bfe3fbe23de4b622",
        "production": "docker",
        "release": "6.0"
    },
    "master_node_uid": "e524e0c6-a507-43b0-b71a-63222eb9f597",
    "unallocated_nodes_num": 1,
    "user_information": {
        "company": "mmm",
        "contact_info_provided": True,
        "email": "test@localhost",
        "name": "Vasia"
    }
}
