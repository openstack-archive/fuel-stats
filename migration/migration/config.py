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

import logging

LOG_FILE = "/var/log/migration.log"
LOG_LEVEL = logging.INFO
LOG_FILE_SIZE = 2048000
LOG_FILES_COUNT = 20

ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200

SYNC_EVERY_SECONDS = 3600

DB_CONNECTION_STRING = "postgresql://collector:***@localhost/collector"
# size of chunk for fetching objects for synchronization
# into Elasticsearch
DB_SYNC_CHUNK_SIZE = 1000

INDEX_MIGRATION = "migration"
DOC_TYPE_MIGRATION_INFO = "info"
MAPPING_MIGRATION = {
    DOC_TYPE_MIGRATION_INFO: {
        "properties": {
            # from
            "db_table_name": {
                "type": "string",
                "index": "not_analyzed"
            },
            "db_id_name": {
                "type": "string",
                "index": "not_analyzed"
            },
            "db_sync_field_name": {
                "type": "string",
                "index": "not_analyzed"
            },
            # to
            "index_name": {
                "type": "string",
                "index": "not_analyzed"
            },
            "doc_type_name": {
                "type": "string",
                "index": "not_analyzed"
            },
            # status
            "last_sync_value": {
                "enabled": False
            },
            "last_sync_time": {
                "type": "date"
            }
        }
    }
}

INDEX_FUEL = "fuel"
DOC_TYPE_STRUCTURE = "structure"
DOC_TYPE_ACTION_LOGS = "action_logs"

MAPPING_FUEL = {
    DOC_TYPE_STRUCTURE: {
        "properties": {
            "master_node_uid": {
                "type": "string",
                "index": "not_analyzed"
            },
            "allocated_nodes_num": {"type": "long"},
            "unallocated_nodes_num": {"type": "long"},
            "creation_date": {"type": "date"},
            "modification_date": {"type": "date"},
            "clusters": {
                "type": "nested",
                "properties": {
                    "id": {"type": "long"},
                    "status": {"type": "string"},
                    "release": {
                        "type": "nested",
                        "properties": {
                            "version": {
                                "type": "string",
                                "index": "not_analyzed"
                            },
                            "os": {
                                "type": "string",
                                "index": "analyzed",
                                "analyzer": "not_analyzed_lowercase"
                            },
                            "name": {
                                "type": "string",
                                "index": "not_analyzed"
                            }
                        }
                    },
                    "attributes": {
                        "type": "nested",
                        "properties": {
                            "libvirt_type": {
                                "type": "string",
                                "index": "not_analyzed"
                            }
                        }
                    },
                    "nodes_num": {"type": "long"},
                    "nodes": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "long"},
                            "manufacturer": {"type": "string"}
                        }
                    },
                }
            }
        }
    },
    DOC_TYPE_ACTION_LOGS: {
        "properties": {
            "master_node_uid": {
                "type": "string",
                "index": "not_analyzed"
            },
            "id": {"type": "long"},
            "actor_id": {"type": "string"},
            "action_group": {"type": "string"},
            "action_name": {"type": "string"},
            "action_type": {"type": "string"},
            "start_timestamp": {"type": "date"},
            "end_timestamp": {"type": "date"},
            "additional_info": {
                "type": "object",
                "properties": {
                    # http request
                    "request_data": {"type": "object"},
                    "response_data": {"type": "object"},
                    # task
                    "parent_task_id": {"type": "long"},
                    "subtasks_ids": {"type": "long"},
                    "operation": {"type": "string"},
                    "nodes_from_resp": {"enabled": "false"},
                    "ended_with_status": {"type": "string"},
                    "message": {"type": "string"},
                    "output": {"enabled": False}
                }
            },
            "is_sent": {"type": "boolean"},
            "cluster_id": {"type": "long"},
            "task_uuid": {"type": "string"}
        }
    }
}

ANALYSIS_INDEX_FUEL = {
    "analyzer": {
        "not_analyzed_lowercase": {
            "filter": ["lowercase"],
            "type": "custom",
            "tokenizer": "keyword"
        }
    }
}

STRUCTURES_DB_TABLE_NAME = "installation_structures"
ACTION_LOGS_DB_TABLE_NAME = "action_logs"

INFO_TEMPLATES = {
    STRUCTURES_DB_TABLE_NAME: {
        "db_table_name": STRUCTURES_DB_TABLE_NAME,
        "db_id_name": "id",
        "db_sync_field_name": "modification_date",
        "last_sync_value": "1970-01-01T00:00:00",
        "index_name": "fuel",
        "doc_type_name": "structure",
        "last_sync_time": None
    },
    ACTION_LOGS_DB_TABLE_NAME: {
        "db_table_name": ACTION_LOGS_DB_TABLE_NAME,
        "db_id_name": "id",
        "db_sync_field_name": "id",
        "last_sync_value": 0,
        "index_name": "fuel",
        "doc_type_name": "action_logs",
        "last_sync_time": None
    }
}
