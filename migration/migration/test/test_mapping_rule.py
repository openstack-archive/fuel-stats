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

import six

from migration.test.base import MigrationTest

from migration.db import db_session
from migration.migrator import MappingRule
from migration.migrator import NameMapping
from migration.model import InstallationStructure


class MappingRuleTest(MigrationTest):

    def test_mapping_rule(self):
        mn_uid = self.create_dumb_structure()
        db_obj = db_session.query(InstallationStructure).filter(
            InstallationStructure.master_node_uid == mn_uid).one()
        rule = MappingRule(
            ('master_node_uid',),
            json_fields=('structure',),
            mixed_fields_mapping=(
                NameMapping(source='creation_date', dest='creation_date'),
                NameMapping(source='modification_date',
                            dest='modification_date')
            )
        )
        index = 'index',
        doc_type = 'doc_type'
        doc = rule.make_doc(index, doc_type, db_obj)
        doc_source = doc['_source']
        self.assertIn('creation_date', doc_source)
        self.assertIn('modification_date', doc_source)
        self.assertEquals(index, doc['_index'])
        self.assertEquals(doc_type, doc['_type'])
        self.assertEquals(db_obj.master_node_uid, doc['_id'])
        for struct_key in six.iterkeys(db_obj.structure):
            self.assertIn(struct_key, doc_source)
