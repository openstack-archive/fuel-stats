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

from collector.api.app import db


class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    __table_args__ = (
        db.UniqueConstraint('node_aid', 'external_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    node_aid = db.Column(db.String, nullable=False)
    external_id = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)


class InstallationStruct(db.Model):
    __tablename__ = 'installation_structs'

    id = db.Column(db.Integer, primary_key=True)
    aid = db.Column(db.String, nullable=False, unique=True)
    struct = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime)
    modification_date = db.Column(db.DateTime)
