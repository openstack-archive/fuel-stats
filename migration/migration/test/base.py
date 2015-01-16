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

from collections import namedtuple
import datetime
from elasticsearch import Elasticsearch
import random
from unittest2.case import TestCase
import uuid

from migration import config
from migration.test.test_env import configure_test_env

# configuring test environment
configure_test_env()

from migration.db import db_session
from migration.db import engine
from migration.migrator import Migrator
from migration.model import ActionLog
from migration.model import InstallationStructure


class BaseTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        configure_test_env()


class DbTest(TestCase):

    def setUp(self):
        super(DbTest, self).setUp()
        db_session.execute('DROP TABLE IF EXISTS action_logs')
        db_session.execute('DROP TABLE IF EXISTS installation_structures')
        db_session.commit()
        InstallationStructure.__table__.create(bind=engine)
        ActionLog.__table__.create(bind=engine)


class ElasticTest(TestCase):

    es = Elasticsearch(hosts=[
        {'host': config.ELASTIC_HOST,
         'port': config.ELASTIC_PORT}
    ])

    def setUp(self):
        super(ElasticTest, self).setUp()
        migrator = Migrator()
        migrator.remove_indices()
        migrator.create_indices()
        self.es.cluster.health(wait_for_status='yellow', request_timeout=1)

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
            'release': random.choice(("6.0-techpreview", "6.0-ga")),
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
        structures = []
        for _ in xrange(installations_num):
            structure = self.generate_structure()
            self.es.index(config.INDEX_FUEL, config.DOC_TYPE_STRUCTURE,
                          body=structure, id=structure['master_node_uid'])
            structures.append(structure)
        self.es.indices.refresh(config.INDEX_FUEL)
        return structures


class MigrationTest(ElasticTest, DbTest):

    def setUp(self):
        super(MigrationTest, self).setUp()

    def create_dumb_structure(self, set_md=True):
        mn_uid = '{}'.format(uuid.uuid4())
        structure = {
            'master_node_uid': mn_uid,
            'fuel_release': {
                'release': 'r',
                'ostf_sha': 'o_sha',
                'astute_sha': 'a_sha',
                'nailgun_sha': 'n_sha',
                'fuellib_sha': 'fl_sha',
                'feature_groups': ['experimental'],
                'api': 'v1'
            },
            'allocated_nodes_num': 0,
            'unallocated_nodes_num': 10,
            'clusters_num': 1,
            'clusters': []
        }
        now = datetime.datetime.utcnow()
        if set_md:
            m_date = now
        else:
            m_date = None
        db_session.add(InstallationStructure(master_node_uid=mn_uid,
                                             structure=structure,
                                             creation_date=now,
                                             modification_date=m_date))
        db_session.commit()
        return mn_uid

    def _action_name(self):
        return random.choice([
            'deploy',
            'deployment',
            'provision',
            'stop_deployment',
            'reset_environment',
            'update',
        ])

    def _gen_id(self):
        return random.randint(1, 10000)

    def _task_status(self):
        return random.choice([
            'ready',
            'running',
            'error'
        ])

    def _nodes(self):
        return [self._gen_id() for _ in xrange(0, 100)]

    def _subtasks(self):
        return [self._gen_id() for _ in xrange(0, 5)]

    def create_dumb_action_log(self, mn_uid=None):
        if mn_uid is None:
            mn_uid = '{}'.format(uuid.uuid4())
        external_id = self._gen_id()
        body = {
            'id': self._gen_id(),
            'actor_id': '{}'.format(uuid.uuid4()),
            'action_group': random.choice([
                'cluster_changes',
                'cluster_checking',
                'operations'
            ]),
            'action_name': self._action_name(),
            'action_type': random.choice(['http_request',
                                          'nailgun_task']),
            'start_timestamp': datetime.datetime.utcnow().isoformat(),
            'end_timestamp': random.choice([
                None,
                (datetime.datetime.utcnow() + datetime.timedelta(
                    seconds=random.randint(0, 60)
                )).isoformat(),
            ]),
            'is_sent': random.choice([True, False]),
            'cluster_id': self._gen_id(),
            'task_uuid': '{}'.format(uuid.uuid4()),
            'additional_info': random.choice([
                {
                    # http request
                    'request_data': {},
                    'response_data': {},
                },
                {
                    # task
                    'parent_task_id': self._gen_id(),
                    'subtasks_ids': self._subtasks(),
                    'operation': self._action_name(),
                    'nodes_from_resp': self._nodes(),
                    'ended_with_status': self._task_status()
                }
            ])
        }
        db_session.add(ActionLog(master_node_uid=mn_uid,
                                 external_id=external_id,
                                 body=body))
        db_session.commit()
        return '{0}_{1}'.format(mn_uid, external_id)


AggsCheck = namedtuple('AggsCheck', ['key', 'doc_count'])
