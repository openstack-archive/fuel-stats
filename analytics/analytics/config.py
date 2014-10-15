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

INDEX_FUEL = 'fuel'
DOC_TYPE_STRUCTURE = 'structure'

INDEXES_MAPPINGS = {
    INDEX_FUEL: {
        DOC_TYPE_STRUCTURE: {
            'properties': {
                'master_node_uid': {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                'allocated_nodes_num': {'type': 'long'},
                'unallocated_nodes_num': {'type': 'long'},
                'clusters': {
                    'type': 'nested',
                    'properties': {
                        'id': {'type': 'long'},
                        'status': {'type': 'string'},
                        'release': {
                            'type': 'nested',
                            'properties': {
                                'version': {
                                    'type': 'string',
                                    'index': 'not_analyzed'
                                },
                                'os': {
                                    'type': 'string',
                                    'index': 'analyzed',
                                    'analyzer': 'not_analyzed_lowercase'
                                },
                                'name': {
                                    'type': 'string',
                                    'index': 'not_analyzed'
                                }
                            }
                        },
                        'nodes_num': {'type': 'long'},
                        'nodes': {
                            'type': 'nested',
                            'properties': {
                                'id': {'type': 'long'}
                            }
                        }
                    }
                }
            }
        }
    }
}


INDEXES_ANALYSIS = {
    INDEX_FUEL: {
        'analyzer': {
            'not_analyzed_lowercase': {
                'filter': ['lowercase'],
                'type': 'custom',
                'tokenizer': 'keyword'
            }
        }
    }
}
