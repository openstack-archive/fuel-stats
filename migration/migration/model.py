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

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base

meta = MetaData()
Base = declarative_base(metadata=meta)


class ActionLog(Base):
    __tablename__ = 'action_logs'
    __table_args__ = (
        UniqueConstraint('master_node_uid', 'external_id'),
    )

    id = Column(Integer, primary_key=True)
    master_node_uid = Column(String, nullable=False)
    external_id = Column(Integer, nullable=False)
    body = Column(JSON, nullable=False)


class InstallationStructure(Base):
    __tablename__ = 'installation_structures'

    id = Column(Integer, primary_key=True)
    master_node_uid = Column(String, nullable=False, unique=True)
    structure = Column(JSON, nullable=False)
    creation_date = Column(DateTime)
    modification_date = Column(DateTime)
    is_filtered = Column(Boolean)
