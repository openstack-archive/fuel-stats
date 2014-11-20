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
from elasticsearch import helpers

from migration import config
from migration.db import db_session
from migration.log import logger
from migration.model import ActionLog
from migration.model import InstallationStructure


class SyncInfo(dict):

    # explicit properties definition
    db_table_name = None
    db_id_name = None
    db_sync_field_name = None
    index_name = None
    doc_type_name = None
    last_sync_value = None
    last_sync_time = None

    def __init__(self, *args, **kwargs):
        super(SyncInfo, self).__init__(*args, **kwargs)
        self.__dict__ = self


NameMapping = namedtuple('NameMapping', ['source', 'dest'])


class MappingRule(object):

    def __init__(self, db_id_name, json_fields=(), mixed_fields_mapping=()):
        """Describes how db object is mapped into Eslasticsearch document
        :param db_id_name: NameMapping of db id field name
        :param json_fields: tuple of fields to be merged as dicts into
        Elasicsearch document
        :param mixed_fields_mapping: tuple of NameMapping for adding into
        Elasicsearch document
        """
        self.db_id_name = db_id_name
        self.json_fields = json_fields
        self.mixed_fields_mapping = mixed_fields_mapping

    def make_doc(self, index_name, doc_type_name, db_object):
        """Returns dictionary for sending into Elasticsearch
        """
        data = {}
        for json_field in self.json_fields:
            data.update(getattr(db_object, json_field))
        for mixed_field in self.mixed_fields_mapping:
            data[mixed_field.dest] = getattr(db_object, mixed_field.source)
        return {
            '_index': index_name,
            '_type': doc_type_name,
            '_id': getattr(db_object, self.db_id_name),
            '_source': data
        }


class Migrator(object):

    def __init__(self):
        self.es = Elasticsearch(hosts=[
            {'host': config.ELASTIC_HOST,
             'port': config.ELASTIC_PORT}])
        self.db_session = db_session

    def remove_indices(self):
        logger.debug("Removing indices in the Elasticsearch")
        for index in (config.INDEX_MIGRATION, config.INDEX_FUEL):
            self.es.indices.delete(index, ignore=[404])
            logger.debug("Index %s is removed from Elasticsearch", index)
        logger.debug("Indices are removed from the Elasticsearch")

    def create_indices(self):
        logger.debug("Creating indices in the Elasticsearch")
        # creating fuel index
        settings = {
            'mappings': config.MAPPING_FUEL,
            'settings': {
                'analysis': config.ANALYSIS_INDEX_FUEL
            }
        }
        self.es.indices.create(config.INDEX_FUEL, body=settings, ignore=[400])
        logger.debug("Index %s is created", config.INDEX_FUEL)

        # creating mapping index
        settings = {
            'mappings': config.MAPPING_MIGRATION
        }
        self.es.indices.create(config.INDEX_MIGRATION, body=settings,
                               ignore=[400])
        logger.debug("Index %s is created", config.INDEX_MIGRATION)
        logger.debug("Indices in the Elasticsearch is created")

    def get_sync_info(self, sync_db_table):
        if self.es.exists(config.INDEX_MIGRATION, sync_db_table,
                          doc_type=config.DOC_TYPE_MIGRATION_INFO):
            logger.debug("Sync_info for %s existed", sync_db_table)
            result = self.es.get(config.INDEX_MIGRATION, sync_db_table,
                                 doc_type=config.DOC_TYPE_MIGRATION_INFO)
            return SyncInfo(result['_source'])
        else:
            logger.debug("Sync_info for %s created from template",
                         sync_db_table)
            return SyncInfo(config.INFO_TEMPLATES.get(sync_db_table, {}))

    def put_sync_info(self, sync_info):
        logger.debug("Putting sync_info %s into Elasticsearch", sync_info)
        self.es.index(config.INDEX_MIGRATION, config.DOC_TYPE_MIGRATION_INFO,
                      sync_info, id=sync_info.db_table_name)

    def migrate_installation_structure(self):
        logger.info("Migration of installation structures is started")
        mapping_rule = MappingRule(
            'master_node_uid',
            json_fields=('structure',),
            mixed_fields_mapping=(
                NameMapping(source='creation_date', dest='creation_date'),
                NameMapping(source='modification_date',
                            dest='modification_date')
            ))
        info = self.get_sync_info(config.STRUCTURES_DB_TABLE_NAME)
        try:
            self.make_migration(InstallationStructure, info, mapping_rule)
            logger.info("Migration of installation structures is finished")
        except Exception:
            logger.exception("Migration of installation structures is failed")

    def migrate_action_logs(self):
        logger.info("Migration of action logs is started")
        mapping_rule = MappingRule(
            'master_node_uid',
            json_fields=('body',),
            mixed_fields_mapping=(
                NameMapping(source='master_node_uid', dest='master_node_uid'),
            ))
        info = self.get_sync_info(config.ACTION_LOGS_DB_TABLE_NAME)
        try:
            self.make_migration(ActionLog, info, mapping_rule)
            logger.info("Migration of action logs is finished")
        except Exception:
            logger.exception("Migration of action logs is failed")

    def _migrate_objs(self, objs, sync_info, mapping_rule):
        if len(objs) == 0:
            logger.info("Nothing to be migrated for %s",
                        sync_info.db_table_name)
            self.put_sync_info(sync_info)
            return False
        logger.info("%d %s to be migrated", len(objs),
                    sync_info.db_table_name)
        docs = []
        for obj in objs:
            doc = mapping_rule.make_doc(sync_info.index_name,
                                        sync_info.doc_type_name, obj)
            docs.append(doc)
            last_sync_value = getattr(obj, sync_info.db_sync_field_name)
        processed, errors = helpers.bulk(self.es, docs)
        if errors:
            logger.error("Migration of %s failed: %s",
                         sync_info.db_table_name, errors)
            return False
        else:
            if last_sync_value is not None:
                sync_info.last_sync_value = last_sync_value
            logger.info("Chunk of %s of size %d is migrated",
                        sync_info.db_table_name, len(objs))
            self.put_sync_info(sync_info)
            return True

    def migrate_with_null_sync_field(self, model, sync_info, mapping_rule):
        logger.debug("Migrating %s with NULL %s", sync_info.db_table_name,
                     sync_info.db_sync_field_name)
        sync_field = getattr(model, sync_info.db_sync_field_name)
        id_field = getattr(model, sync_info.db_id_name)
        offset = 0
        while True:
            sync_info.last_sync_time = datetime.datetime.utcnow()
            objs = self.db_session.query(model). \
                filter(sync_field.is_(None)). \
                order_by(id_field.asc()). \
                limit(config.DB_SYNC_CHUNK_SIZE).offset(offset).all()
            offset += len(objs)
            if not self._migrate_objs(objs, sync_info, mapping_rule):
                break
        logger.debug("%s with NULL %s migrated", sync_info.db_table_name,
                     sync_info.db_sync_field_name)

    def migrate_by_sync_field(self, model, sync_info, mapping_rule):
        logger.debug("Migrating %s with %s > %s", sync_info.db_table_name,
                     sync_info.db_sync_field_name, sync_info.last_sync_value)
        sync_field = getattr(model, sync_info.db_sync_field_name)
        id_field = getattr(model, sync_info.db_id_name)
        while True:
            sync_info.last_sync_time = datetime.datetime.utcnow()
            objs = self.db_session.query(model). \
                filter(sync_field > sync_info.last_sync_value). \
                order_by(id_field.asc()). \
                limit(config.DB_SYNC_CHUNK_SIZE).all()

            if not self._migrate_objs(objs, sync_info, mapping_rule):
                break
        logger.debug("%s with %s > %s migrated", sync_info.db_table_name,
                     sync_info.db_sync_field_name, sync_info.last_sync_value)

    def make_migration(self, model, sync_info, mapping_rule):
        self.migrate_with_null_sync_field(model, sync_info, mapping_rule)
        self.migrate_by_sync_field(model, sync_info, mapping_rule)
