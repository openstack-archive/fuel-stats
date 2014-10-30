
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
import random
import uuid

from migration import config
from migration.test.base import ElasticTest


class Reports(ElasticTest):

    def load_data(self):
        pass

    def gen_id(self, id_range=(0, 1000000)):
        return random.randint(*id_range)

    def generate_node(
            self,
            roles_range=(0, 5),
            node_roles=('compute', 'controller', 'cinder', 'ceph-osd',
                        'zabbix', 'mongo'),
            oses=('Ubuntu', 'CentOs', 'Ubuntu LTS XX'),
            node_statuses = ('ready', 'discover', 'provisioning',
                             'provisioned', 'deploying', 'error')
    ):
        roles = []
        for _ in xrange(random.randint(*roles_range)):
            roles.append(random.choice(node_roles))
        node = {
            'id': self.gen_id(),
            'roles': roles,
            'os': random.choice(oses),
            'status': random.choice(node_statuses)
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
            libvirt_names=('qemu', 'kvm', 'vCenter')
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
                'libvirt_type': random.choice(libvirt_names)
            }
        }
        for _ in xrange(nodes_num):
            cluster['nodes'].append(self.generate_node())
        return cluster

    def generate_structure(
            self,
            clusters_num_range=(0, 10),
            unallocated_nodes_num_range=(0, 20)
    ):
        mn_uid = '{}'.format(uuid.uuid4())
        clusters_num = random.randint(*clusters_num_range)
        fuel_release = {
            'release': "XX",
            'api': 1,
            'nailgun_sha': "Unknown build",
            'astute_sha': "Unknown build",
            'fuellib_sha': "Unknown build",
            'ostf_sha': "Unknown build",
            'feature_groups': ['experimental', 'mirantis']
        }

        structure = {
            'master_node_uid': mn_uid,
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

    def generate_data(self, installations_num=100):
        for _ in xrange(installations_num):
            structure = self.generate_structure()
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE,
                          body=structure, id=structure['master_node_uid'])
        self.es.indices.refresh(config.INDEX_FUEL)

    def test_oses_distribution(self):
        self.generate_data(installations_num=100)
        # nodes oses distribution request
        oses_list = {
            "size": 0,
            "aggs": {
                "clusters": {
                    "nested": {
                        "path": "clusters"
                    },
                    "aggs": {
                        "release": {
                            "nested": {
                                "path": "clusters.release"
                            },
                            "aggs": {
                                "oses": {
                                    "terms": {
                                        "field": "os"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        self.es.search(index=config.INDEX_FUEL,
                       doc_type=config.DOC_TYPE_STRUCTURE,
                       body=oses_list)

    def test_nodes_distribution(self):
        self.generate_data(installations_num=100)
        nodes_distribution = {
            "size": 0,
            "aggs": {
                "nodes_distribution": {
                    "histogram": {
                        "field": "allocated_nodes_num",
                        "interval": 1
                    }
                }
            }
        }
        self.es.search(index=config.INDEX_FUEL,
                       doc_type=config.DOC_TYPE_STRUCTURE,
                       body=nodes_distribution)

    def test_libvirt_type_distribution(self):
        self.generate_data(installations_num=100)
        # nodes oses distribution request
        libvirt_types_req = {
            "size": 0,
            "aggs": {
                "clusters": {
                    "nested": {
                        "path": "clusters"
                    },
                    "aggs": {
                        "attributes": {
                            "nested": {
                                "path": "clusters.attributes"
                            },
                            "aggs": {
                                "libvirt_types": {
                                    "terms": {
                                        "field": "libvirt_type"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        self.es.search(index=config.INDEX_FUEL,
                       doc_type=config.DOC_TYPE_STRUCTURE,
                       body=libvirt_types_req)
