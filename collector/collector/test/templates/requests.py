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
                'nodes_num': len(nodes)
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
                "type": "action_type-1",
                "name": "action_name-1"
            },
            'action_group-2': {
                "type": "action_type-2",
                "name": "action_name-2"
            },
            'action_group-3': {
                "type": "action_type-3",
                "name": "action_name-3"
            },
            'action_group-4': {
                "type": "action_type-4",
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
                    "action_name": self.actions[action_group]['type'],
                    "action_type": self.actions[action_group]['name'],
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
