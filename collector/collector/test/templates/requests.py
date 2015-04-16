#    Copyright 2014 Mirantis, Inc.
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

import datetime
import json
import random

from bisect import bisect


class BaseRequestTemplate(object):

    def __init__(self):

        self.headers = [
            '[Content-Type: application/json]',
            '[Connection: close]',
            '[User-Agent: Tank]'
        ]

        self.fuel_releases = {
            '6.0': [
                {
                    'version': '2014.2-6.0',
                    'os': 'Ubuntu',
                    'name': 'Juno on Ubuntu 12.04.04'
                },
                {
                    'version': '2014.2-6.0',
                    'os': 'CentOS',
                    'name': 'Juno on CentOS 6.5'
                }
            ],
            '6.0.1': [
                {
                    'version': '2014.2-6.0.1',
                    'os': 'Ubuntu',
                    'name': 'Juno on Ubuntu 12.04.05'
                },
                {
                    'version': '2014.2-6.0.1',
                    'os': 'CentOS',
                    'name': 'Juno on CentOS 6.6'
                }
            ]
        }

        self.cluster_statuses = ['new',
                                 'operational',
                                 'error']

        self.nodes_roles = ['controller',
                            'compute',
                            'mongodb',
                            'ceph-osd',
                            'cinder',
                            'zabbix']

        self.nodes_statuses = ['ready',
                               'discovered',
                               'provisioned',
                               'provisioning',
                               'deploying',
                               'deployed',
                               'error']

        self.api_versions = ['v1', 'v2']
        self.feature_groups = ['mirantis', 'experimental']

    @property
    def random_sha(self):
        return ''.join(random.choice('abcdef0123456789') for _ in xrange(40))

    @property
    def fuel_release(self):
        return {
            "ostf_sha": self.random_sha,
            "nailgun_sha": self.random_sha,
            "astute_sha": self.random_sha,
            "fuellib_sha": self.random_sha,
            "api": random.choice(self.api_versions),
            "release": random.choice(self.fuel_releases.keys()),
            "feature_groups": random.sample(
                self.feature_groups,
                random.randint(1, len(self.feature_groups)))
        }


class InstallationRequestTemplate(BaseRequestTemplate):

    def __init__(self, max_clusters_count=10, max_cluster_size=100):
        BaseRequestTemplate.__init__(self)
        self.max_clusters_count = max_clusters_count
        self.max_cluster_size = max_cluster_size
        self.url = "/api/v1/installation_structure/"

    @property
    def clusters_number(self):
        return random.randint(1, self.max_clusters_count)

    @property
    def nodes_number(self):
        return random.randint(1, self.max_cluster_size)

    def get_request_body(self):
        release = self.fuel_release
        clusters_number = self.clusters_number
        allocated_nodes = 0
        unallocated_nodes = self.nodes_number

        clusters = []
        for cluster_id in xrange(1, clusters_number):
            nodes = []
            nodes_number = self.nodes_number
            allocated_nodes += nodes_number
            for node_id in xrange(1, nodes_number):
                node = {
                    'status': random.choice(self.nodes_statuses),
                    'id': node_id,
                    'roles': random.sample(
                        self.nodes_roles,
                        random.randint(1, len(self.nodes_roles)))
                }
                nodes.append(node)

            controllers = [n for n in nodes if 'controller' in n['roles']]

            cluster = {
                'release': random.choice(
                    self.fuel_releases.get(release["release"])),
                'nodes': nodes,
                'id': cluster_id,
                'mode': 'ha_full' if len(controllers) > 1 else 'multinode',
                'nodes_num': len(nodes),
                'status': random.choice(self.cluster_statuses),
                'attributes': {},
            }
            clusters.append(cluster)

        data = {
            "installation_structure": {
                "master_node_uid": self.random_sha,
                "clusters_num": clusters_number,
                "allocated_nodes_num": allocated_nodes,
                "unallocated_nodes_num": unallocated_nodes,
                "fuel_release": release,
                "clusters": clusters
            }
        }

        return json.dumps(data)


class ActionLogRequestTemplate(BaseRequestTemplate):

    def __init__(self, max_logs_count=30):
        BaseRequestTemplate.__init__(self)
        self.max_logs_count = max_logs_count
        self.url = "/api/v1/action_logs/"
        self.actions = {
            'action_group-1': {
                "type": "nailgun_task",
                "name": "action_name-1"
            },
            'action_group-2': {
                "type": "nailgun_task",
                "name": "action_name-2"
            },
            'action_group-3': {
                "type": "http_request",
                "name": "action_name-3"
            },
            'action_group-4': {
                "type": "http_request",
                "name": "action_name-4"
            }
        }

    def get_request_body(self):
        actor_id = random.randint(1, 999)
        master_node_uid = self.random_sha
        data = {'action_logs': []}

        for id in xrange(0, self.max_logs_count):
            action_group = random.choice(self.actions.keys())
            action_log = {
                'master_node_uid': master_node_uid,
                'external_id': random.randint(1, 999999),
                'body': {
                    "id": id,
                    "actor_id": str(actor_id),
                    "action_group": action_group,
                    "action_name": self.actions[action_group]['name'],
                    "action_type": self.actions[action_group]['type'],
                    "start_timestamp": str(datetime.datetime.now()),
                    "end_timestamp": str(datetime.datetime.now()),
                    "additional_info": {},
                    "is_sent": False,
                    "cluster_id": random.randint(1, 999),
                    "task_uuid": self.random_sha
                }
            }
            data['action_logs'].append(action_log)

        return json.dumps(data)


class OSwLRequestTemplate(BaseRequestTemplate):

    def __init__(self):
        BaseRequestTemplate.__init__(self)
        self.url = "/api/v1/oswl_stats/"
        self.resources = ['vm', 'tenant', 'volume',
                          'keystone_user', 'flavor', 'image']

    def current_vm(self):
        return {"status": "ACTIVE", "tenant_id": self.random_sha,
                "created_at": str(datetime.datetime.now()),
                "image_id": self.random_sha, "flavor_id": self.random_sha,
                "power_state": 1, "time": "15:56:12.146313",
                "host_id": self.random_sha, "id": self.random_sha}

    def modified_vm(self):
        return {"status": "ACTIVE", "power_state": 1,
                "time": "20:56:12.146313", "id": self.random_sha}

    def current_image(self):
        return {"created_at": str(datetime.datetime.now()), "minDisk": 0,
                "updated_at": str(datetime.datetime.now()),
                "sizeBytes": 14024704, "minRam": 64, "id": self.random_sha}

    def modified_image(self):
        return {"minDisk": 0, "updated_at": str(datetime.datetime.now()),
                "time": "19:50:12.146313", "id": self.random_sha}

    def current_volume(self):
        return {"status": "available", "attachments": [],
                "availability_zone": "nova", "bootable_flag": "true",
                "tenant_id": self.random_sha, "encrypted_flag": 'false',
                "volume_type": "None",
                "host": "node-3.test.domain.local#DEFAULT",
                "time": "14:13:06.001065", "snapshot_id": 'null',
                "id": self.random_sha, "size": 1}

    def modified_volume(self):
        return {"status": "available", "attachments": [],
                "time": "18:13:06.001065", "id": self.random_sha}

    def current_tenant(self):
        return {"enabled_flag": 'true', "id": self.random_sha}

    def current_user(self):
        return {"enabled_flag": 'true', "tenant_id": self.random_sha,
                "id": self.random_sha}

    def current_flavor(self):
        return {"ram": 512, "ephemeral": 0, "vcpus": 1, "swap": "",
                "disk": 1, "id": self.random_sha}

    def added(self):
        return {"id": self.random_sha, "time": "15:51:11.690102"}

    def weighted_choice(self, choices):
        """Converts SqlAlchemy object to dict serializable to json
        :param choices: list of tuples with probability and choice value
        :return: choice value
        """
        values, weights = zip(*choices)
        total = 0
        cum_weights = []
        for w in weights:
            total += w
            cum_weights.append(total)
        x = random.random() * total
        i = bisect(cum_weights, x)
        return values[i]

    def real_data(self):
        return {
            "1": {
            "vm": {"current": [self.current_vm()], "removed": [],
                   "added": [self.added()], "modified": [self.modified_vm()]},
            "image": {"current": [self.current_image()], "removed": [],
                      "added": [self.added()],
                      "modified": [self.modified_image()]},
            "volume": {"current": [self.current_volume()], "removed": [],
                       "added": [self.added()],
                       "modified": [self.modified_volume()]},
            "tenant": {"current": [self.current_tenant()], "removed": [],
                       "added": [self.added()],
                       "modified": [self.current_tenant()]},
            "keystone_user": {"current": [self.current_user()], "removed": [],
                              "added": [self.added()],
                              "modified": [self.current_user()]},
            "flavor": {"current": [self.current_flavor()], "removed": [],
                       "added": [self.added()], "modified": []}
            },
            "3": {
            "vm": {"current": [self.current_vm() for i in range(5)],
                   "removed": [self.current_vm() for i in range(1)],
                   "added": [self.added() for i in range(5)],
                   "modified": [self.modified_vm() for i in range(5)]},
            "image": {"current": [self.current_image() for i in range(3)],
                      "removed": [self.current_image() for i in range(1)],
                      "added": [self.added() for i in range(3)],
                      "modified": [self.modified_image() for i in range(3)]},
            "volume": {"current": [self.current_volume() for i in range(2)],
                       "removed": [],
                       "added": [self.added() for i in range(2)],
                       "modified": [self.modified_volume()
                                    for i in range(2)]},
            "tenant": {"current": [self.current_tenant() for i in range(9)],
                       "removed": [self.current_tenant() for i in range(1)],
                       "added": [self.added() for i in range(9)],
                       "modified": [self.current_tenant() for i in range(6)]},
            "keystone_user": {"current": [self.current_user()
                                          for i in range(8)],
                              "removed": [self.current_user()
                                          for i in range(2)],
                              "added": [self.added() for i in range(8)],
                              "modified": [self.current_user()
                                           for i in range(4)]},
            "flavor": {"current": [self.current_flavor() for i in range(8)],
                       "removed": [self.current_flavor()
                                   for i in range(2)],
                       "added": [self.added() for i in range(8)],
                       "modified": []}
            },
            "5": {
            "vm": {"current": [self.current_vm() for i in range(10)],
                   "removed": [self.current_vm() for i in range(1)],
                   "added": [self.added() for i in range(10)],
                   "modified": [self.modified_vm() for i in range(10)]},
            "image": {"current": [self.current_image() for i in range(5)],
                      "removed": [self.current_image() for i in range(1)],
                      "added": [self.added() for i in range(5)],
                      "modified": [self.modified_image() for i in range(3)]},
            "volume": {"current": [self.current_volume() for i in range(3)],
                       "removed": [],
                       "added": [self.added() for i in range(3)],
                       "modified": [self.modified_volume()
                                    for i in range(2)]},
            "tenant": {"current": [self.current_tenant() for i in range(9)],
                       "removed": [self.current_tenant() for i in range(1)],
                       "added": [self.added() for i in range(9)],
                       "modified": [self.current_tenant() for i in range(6)]},
            "keystone_user": {"current": [self.current_user()
                                          for i in range(8)],
                              "removed": [self.current_user()
                                          for i in range(2)],
                              "added": [self.added() for i in range(8)],
                              "modified": [self.current_user()
                                           for i in range(4)]},
            "flavor": {"current": [self.current_flavor() for i in range(8)],
                       "removed": [self.current_flavor() for i in range(2)],
                       "added": [self.added() for i in range(8)],
                       "modified": []}
            },
            "10": {
            "vm": {"current": [self.current_vm() for i in range(50)],
                   "removed": [self.current_vm() for i in range(10)],
                   "added": [self.added() for i in range(50)],
                   "modified": [self.modified_vm() for i in range(50)]},
            "image": {"current": [self.current_image() for i in range(7)],
                      "removed": [self.current_image() for i in range(1)],
                      "added": [self.added() for i in range(7)],
                      "modified": [self.modified_image() for i in range(5)]},
            "volume": {"current": [self.current_volume() for i in range(10)],
                       "removed": [],
                       "added": [self.added() for i in range(10)],
                       "modified": [self.modified_volume()
                                    for i in range(10)]},
            "tenant": {"current": [self.current_tenant() for i in range(9)],
                       "removed": [self.current_tenant() for i in range(1)],
                       "added": [self.added() for i in range(9)],
                       "modified": [self.current_tenant() for i in range(6)]},
            "keystone_user": {"current": [self.current_user()
                                          for i in range(8)],
                              "removed": [self.current_user()
                                          for i in range(2)],
                              "added": [self.added() for i in range(8)],
                              "modified": [self.current_user()
                                           for i in range(5)]},
            "flavor": {"current": [self.current_flavor() for i in range(10)],
                       "removed": [self.current_flavor() for i in range(2)],
                       "added": [self.added() for i in range(10)],
                       "modified": []}
            },
            "20": {
            "vm": {"current": [self.current_vm() for i in range(100)],
                   "removed": [self.current_vm() for i in range(10)],
                   "added": [self.added() for i in range(100)],
                   "modified": [self.modified_vm() for i in range(75)]},
            "image": {"current": [self.current_image() for i in range(10)],
                      "removed": [self.current_image() for i in range(1)],
                      "added": [self.added() for i in range(10)],
                      "modified": [self.modified_image() for i in range(5)]},
            "volume": {"current": [self.current_volume() for i in range(10)],
                       "removed": [],
                       "added": [self.added() for i in range(10)],
                       "modified": [self.modified_volume()
                                    for i in range(10)]},
            "tenant": {"current": [self.current_tenant() for i in range(9)],
                       "removed": [self.current_tenant() for i in range(1)],
                       "added": [self.added() for i in range(9)],
                       "modified": [self.current_tenant() for i in range(9)]},
            "keystone_user": {"current": [self.current_user()
                                          for i in range(8)],
                              "removed": [self.current_user()
                                          for i in range(2)],
                              "added": [self.added() for i in range(8)],
                              "modified": [self.current_user()
                                           for i in range(6)]},
            "flavor": {"current": [self.current_flavor() for i in range(10)],
                       "removed": [self.current_flavor() for i in range(2)],
                       "added": [self.added() for i in range(10)],
                       "modified": []}
            },
            "50": {
            "vm": {"current": [self.current_vm() for i in range(250)],
                   "removed": [self.current_vm() for i in range(20)],
                   "added": [self.added() for i in range(250)],
                   "modified": [self.modified_vm() for i in range(125)]},
            "image": {"current": [self.current_image() for i in range(10)],
                      "removed": [self.current_image() for i in range(1)],
                      "added": [self.added() for i in range(10)],
                      "modified": [self.modified_image() for i in range(5)]},
            "volume": {"current": [self.current_volume() for i in range(10)],
                       "removed": [],
                       "added": [self.added() for i in range(10)],
                       "modified": [self.modified_volume()
                                    for i in range(10)]},
            "tenant": {"current": [self.current_tenant() for i in range(9)],
                       "removed": [self.current_tenant() for i in range(1)],
                       "added": [self.added() for i in range(9)],
                       "modified": [self.current_tenant() for i in range(9)]},
            "keystone_user": {"current": [self.current_user()
                                          for i in range(8)],
                              "removed": [self.current_user()
                                          for i in range(2)],
                              "added": [self.added() for i in range(8)],
                              "modified": [self.current_user()
                                           for i in range(8)]},
            "flavor": {"current": [self.current_flavor() for i in range(10)],
                       "removed": [self.current_flavor() for i in range(2)],
                       "added": [self.added() for i in range(10)],
                       "modified": []}
            }
        }

    def get_request_body(self):
        master_node_uid = self.random_sha
        data = {'oswl_stats': []}
        choice = self.weighted_choice([("1", 5), ("3", 10), ("5", 15),
                                       ("10", 20), ("20", 40), ("50", 10)])

        for type in ['vm', 'image', 'volume', 'tenant', 'keystone_user',
                     'flavor']:
            oswl_stat = {
                'master_node_uid': master_node_uid,
                "id": random.randint(1, 100),
                "cluster_id": random.randint(1, 999),
                'created_date': str(datetime.datetime.now()),
                'updated_time': str(datetime.datetime.now()),
                'resource_type': type,
                'resource_checksum': self.random_sha,
                'resource_data': self.real_data()[choice][type]
            }
            data['oswl_stats'].append(oswl_stat)

        return json.dumps(data)
