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
import functools
from elasticsearch import Elasticsearch
from random import randint
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

    def create_dumb_action_log(self):
        mn_uid = '{}'.format(uuid.uuid4())
        gen_id = functools.partial(randint, 1, 10000)
        external_id = gen_id()
        body = {
            'id': gen_id(),
            "actor_id": uuid.uuid4(),
            # "action_group": {"type": "string"},
            # "action_name": {"type": "string"},
            # "action_type": {"type": "string"},
            # "start_timestamp": {"type": "date"},
            # "end_timestamp": {"type": "date"},
            # "additional_info": {
            #     "type": "object",
            #     "properties": {
            #         # http request
            #         "request_data": {"type": "object"},
            #         "response_data": {"type": "object"},
            #         # task
            #         "parent_task_id": {"type": "long"},
            #         "subtasks_ids": {"type": "long"},
            #         "operation": {"type": "string"},
            #         "nodes_from_resp": {"type": "long"},
            #         "ended_with_status": {"type": "string"}
            #     }
            # },
            # "is_sent": {"type": "boolean"},
            # "cluster_id": {"type": "long"},
            # "task_uuid": {"type": "string"}
        }
        db_session.add(ActionLog(master_node_uid=mn_uid,
                                 external_id=external_id,
                                 body=body))
        db_session.commit()
        return mn_uid


AggsCheck = namedtuple('AggsCheck', ['key', 'doc_count'])
