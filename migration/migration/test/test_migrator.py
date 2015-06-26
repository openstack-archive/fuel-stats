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
from dateutil import parser
from migration import config
from mock import patch

from migration.test.base import MigrationTest

from migration.migrator import Migrator
from migration.model import ActionLog as AL
from migration.model import InstallationStructure as IS


class MigratorTest(MigrationTest):

    def test_indices_creation(self):
        migrator = Migrator()
        migrator.create_indices()

    def test_db_connection(self):
        migrator = Migrator()
        result = migrator.db_session.execute("SELECT '1'")
        result.fetchone()

    def test_get_sync_info(self):
        migrator = Migrator()

        # checking unknown table sync info
        self.assertDictEqual({}, migrator.get_sync_info('xxx'))

        # checking not existed info
        self.assertDictEqual(
            config.INFO_TEMPLATES[config.ACTION_LOGS_DB_TABLE_NAME],
            migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)
        )
        self.assertDictEqual(
            config.INFO_TEMPLATES[config.STRUCTURES_DB_TABLE_NAME],
            migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        )

        # checking existed info
        doc = {'db_table_name': config.ACTION_LOGS_DB_TABLE_NAME}
        migrator.es.index(config.INDEX_MIGRATION,
                          config.DOC_TYPE_MIGRATION_INFO,
                          doc, id=config.ACTION_LOGS_DB_TABLE_NAME)
        self.es.indices.refresh(config.INDEX_MIGRATION)
        self.assertDictEqual(
            doc,
            migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME))

    def test_empty_installation_structure_migration(self):
        migrator = Migrator()
        time_before = datetime.datetime.utcnow()
        info_before = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        migrator.migrate_installation_structure()
        info_after = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        time_of_sync = parser.parse(info_after.last_sync_time)
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)
        self.assertEquals(info_before.last_sync_value,
                          info_after.last_sync_value)

    def get_indexed_docs_num(self, sync_info):
        resp = self.es.count(index=sync_info.index_name,
                             doc_type=sync_info.doc_type_name,
                             body={'query': {'match_all': {}}})
        return resp['count']

    @patch('migration.config.DB_SYNC_CHUNK_SIZE', 2)
    def test_migrations_chain(self):
        migrator = Migrator()
        migrator.migrate_installation_structure()
        migrator.migrate_action_logs()

        docs_num = 3
        for _ in xrange(docs_num):
            self.create_dumb_structure()
            self.create_dumb_action_log()
        is_sync_info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        is_indexed_docs_before = self.get_indexed_docs_num(is_sync_info)
        al_sync_info = migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)
        al_indexed_docs_before = self.get_indexed_docs_num(al_sync_info)

        migrator.migrate_installation_structure()
        migrator.migrate_action_logs()
        self.es.indices.refresh(index=config.INDEX_FUEL)

        is_indexed_docs_after = self.get_indexed_docs_num(is_sync_info)
        self.assertEquals(is_indexed_docs_before + docs_num,
                          is_indexed_docs_after)
        al_indexed_docs_after = self.get_indexed_docs_num(al_sync_info)
        self.assertEquals(al_indexed_docs_before + docs_num,
                          al_indexed_docs_after)

    @patch('migration.config.DB_SYNC_CHUNK_SIZE', 2)
    def test_installation_structure_migration(self):
        mn_uids = set([self.create_dumb_structure() for _ in xrange(3)])
        null_md_uids = set([self.create_dumb_structure(set_md=False)
                            for _ in xrange(3)])
        mn_uids.update(null_md_uids)
        mn_uids.update(set([self.create_dumb_structure() for _ in xrange(3)]))

        migrator = Migrator()
        sync_info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        indexed_docs_before = self.get_indexed_docs_num(sync_info)

        # checking migration
        time_before = datetime.datetime.utcnow()
        migrator.migrate_installation_structure()
        self.es.indices.refresh(index=config.INDEX_MIGRATION)
        new_sync_info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        time_of_sync = parser.parse(new_sync_info.last_sync_time)

        # checking sync time is updated
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)

        # checking last sync id is updated
        last_md = parser.parse(new_sync_info.last_sync_value)
        initial_md = parser.parse(sync_info.last_sync_value)
        self.assertGreater(last_md, initial_md)

        # checking all docs are migrated
        self.es.indices.refresh(index=sync_info.index_name)
        self.assertEquals(indexed_docs_before + len(mn_uids),
                          self.get_indexed_docs_num(sync_info))

        # checking new docs are indexed
        for mn_uid in mn_uids - null_md_uids:
            doc = self.es.get(sync_info.index_name, mn_uid,
                              doc_type=sync_info.doc_type_name)
            # checking datetimes are migrated
            source = doc['_source']
            self.assertIsNotNone(source['creation_date'])
            self.assertIsNotNone(source['modification_date'])

        # checking new docs are indexed
        for mn_uid in null_md_uids:
            doc = self.es.get(sync_info.index_name, mn_uid,
                              doc_type=sync_info.doc_type_name)
            # checking datetimes are migrated
            source = doc['_source']
            self.assertIsNotNone(source['creation_date'])
            self.assertIsNone(source['modification_date'])

    def test_filtered_installation_structure_migration(self):
        docs_num = 100
        mn_uids = set([self.create_dumb_structure() for _ in xrange(docs_num)])

        migrator = Migrator()
        is_filtered_variants = set(obj.is_filtered for obj in
                                   migrator.db_session.query(IS).all())
        self.assertEqual(set((True, False, None)), is_filtered_variants)

        sync_info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        indexed_docs_before = self.get_indexed_docs_num(sync_info)

        migrator.migrate_installation_structure()
        self.es.indices.refresh(index=config.INDEX_FUEL)

        indexed_docs_after = self.get_indexed_docs_num(sync_info)
        self.assertEqual(indexed_docs_before + docs_num, indexed_docs_after)

        # checking docs not contains None
        for mn_uid in mn_uids:
            doc = self.es.get(sync_info.index_name, mn_uid,
                              doc_type=sync_info.doc_type_name)
            # checking datetimes are migrated
            source = doc['_source']
            print "#### source", source['is_filtered']

    @patch('migration.config.DB_SYNC_CHUNK_SIZE', 2)
    def test_null_modification_date_migration(self):
        docs_num = 5
        for _ in xrange(docs_num):
            self.create_dumb_structure(set_md=False)

        migrator = Migrator()
        sync_info_before = migrator.get_sync_info(
            config.STRUCTURES_DB_TABLE_NAME)
        # checking sync info before migrations
        self.assertIsNotNone(sync_info_before.last_sync_value)
        self.assertIsNone(sync_info_before.last_sync_time)
        indexed_docs_before = self.get_indexed_docs_num(sync_info_before)

        # migrating data
        migrator.migrate_installation_structure()
        self.es.indices.refresh(config.INDEX_FUEL)
        self.es.indices.refresh(config.INDEX_MIGRATION)

        # checking sync info after migrations
        sync_info_after = migrator.get_sync_info(
            config.STRUCTURES_DB_TABLE_NAME)
        self.assertIsNotNone(sync_info_after.last_sync_value)
        self.assertIsNotNone(sync_info_after.last_sync_time)
        indexed_docs_after = self.get_indexed_docs_num(sync_info_after)
        self.assertEquals(indexed_docs_before + docs_num, indexed_docs_after)

    def test_empty_action_logs_migration(self):
        migrator = Migrator()
        time_before = datetime.datetime.utcnow()
        migrator.migrate_action_logs()
        info = migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)
        time_of_sync = parser.parse(info.last_sync_time)
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)
        self.assertEquals(0, info.last_sync_value)

    @patch('migration.config.DB_SYNC_CHUNK_SIZE', 2)
    def test_action_logs_migration(self):
        docs_num = 5
        mn_uids = [self.create_dumb_action_log() for _ in xrange(docs_num)]

        migrator = Migrator()
        sync_info = migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)

        indexed_docs_before = self.get_indexed_docs_num(sync_info)

        # checking migration
        time_before = datetime.datetime.utcnow()
        migrator.migrate_action_logs()
        self.es.indices.refresh(index=config.INDEX_MIGRATION)
        new_sync_info = migrator.get_sync_info(
            config.ACTION_LOGS_DB_TABLE_NAME)
        time_of_sync = parser.parse(new_sync_info.last_sync_time)
        last_obj = migrator.db_session.query(AL).order_by(
            AL.id.desc()).first()

        # checking sync time is updated
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)

        # checking last sync id is updated
        self.assertEquals(last_obj.id, new_sync_info.last_sync_value)

        # checking all docs are migrated
        self.es.indices.refresh(index=sync_info.index_name)
        self.assertEquals(indexed_docs_before + docs_num,
                          self.get_indexed_docs_num(sync_info))

        # checking new docs are indexed
        check_keys = [
            'master_node_uid',
            'id',
            'actor_id',
            'action_group',
            'action_name',
            'action_type',
            'start_timestamp',
            'end_timestamp',
            'additional_info',
            'is_sent',
            'cluster_id',
            'task_uuid'
        ]
        for mn_uid in mn_uids:
            resp = self.es.get(sync_info.index_name, mn_uid,
                               doc_type=sync_info.doc_type_name)
            doc = resp['_source']
            for k in check_keys:
                self.assertTrue(k in doc)

    @patch('migration.config.DB_SYNC_CHUNK_SIZE', 2)
    def test_action_logs_one_node_migration(self):
        docs_num = 5
        mn_uid = 'xx'
        for _ in xrange(docs_num):
            self.create_dumb_action_log(mn_uid=mn_uid)

        migrator = Migrator()
        sync_info = migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)
        indexed_docs_before = self.get_indexed_docs_num(sync_info)
        migrator.migrate_action_logs()

        # checking all docs are migrated
        self.es.indices.refresh(index=sync_info.index_name)
        self.assertEquals(indexed_docs_before + docs_num,
                          self.get_indexed_docs_num(sync_info))
