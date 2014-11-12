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
from migration.model import ActionLog
from migration.model import InstallationStructure


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
        migrator.migrate_installation_structure()
        info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        time_of_sync = parser.parse(info.last_sync_time)
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)
        self.assertEquals(0, info.last_sync_id)

    def get_indexed_docs_num(self, sync_info):
        resp = self.es.count(index=sync_info.index_name,
                             doc_type=sync_info.doc_type_name,
                             body={'query': {'match_all': {}}})
        return resp['count']

    @patch('migration.config.DB_SYNC_CHUNK_SIZE', 2)
    def test_installation_structure_migration(self):
        docs_num = 3
        mn_uids = [self.create_dumb_structure() for _ in xrange(docs_num)]

        migrator = Migrator()
        sync_info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        indexed_docs_before = self.get_indexed_docs_num(sync_info)

        # checking migration
        time_before = datetime.datetime.utcnow()
        migrator.migrate_installation_structure()
        self.es.indices.refresh(index=config.INDEX_MIGRATION)
        new_sync_info = migrator.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        time_of_sync = parser.parse(new_sync_info.last_sync_time)
        last_obj = migrator.db_session.query(InstallationStructure).order_by(
            InstallationStructure.id.desc()).first()

        # checking sync time is updated
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)

        # checking last sync id is updated
        self.assertEquals(last_obj.id, new_sync_info.last_sync_id)

        # checking all docs are migrated
        self.es.indices.refresh(index=sync_info.index_name)
        self.assertEquals(indexed_docs_before + docs_num,
                          self.get_indexed_docs_num(sync_info))

        # checking new docs are indexed
        for mn_uid in mn_uids:
            doc = self.es.get(sync_info.index_name, mn_uid,
                              doc_type=sync_info.doc_type_name)
            # checking dates are migrated
            source = doc['_source']
            self.assertIsNotNone(source['creation_date'])
            self.assertIsNotNone(source['modification_date'])

    def test_empty_action_logs_migration(self):
        migrator = Migrator()
        time_before = datetime.datetime.utcnow()
        migrator.migrate_action_logs()
        info = migrator.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)
        time_of_sync = parser.parse(info.last_sync_time)
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)
        self.assertEquals(0, info.last_sync_id)

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
        last_obj = migrator.db_session.query(ActionLog).order_by(
            ActionLog.id.desc()).first()

        # checking sync time is updated
        self.assertLessEqual(time_before, time_of_sync)
        self.assertGreaterEqual(datetime.datetime.utcnow(), time_of_sync)

        # checking last sync id is updated
        self.assertEquals(last_obj.id, new_sync_info.last_sync_id)

        # checking all docs are migrated
        self.es.indices.refresh(index=sync_info.index_name)
        self.assertEquals(indexed_docs_before + docs_num,
                          self.get_indexed_docs_num(sync_info))

        # checking new docs are indexed
        for mn_uid in mn_uids:
            self.es.get(sync_info.index_name, mn_uid,
                        doc_type=sync_info.doc_type_name)
