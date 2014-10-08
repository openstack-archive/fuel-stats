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

"""Collector DB schema

Revision ID: 558f628a238
Revises: None
Create Date: 2014-09-22 15:20:31.405870

"""

# revision identifiers, used by Alembic.
revision = '558f628a238'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'action_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_aid', sa.String(), nullable=False),
        sa.Column('external_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_aid', 'external_id')
    )
    op.create_table(
        'installation_structs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aid', sa.String(), nullable=False),
        sa.Column('struct', sa.Text(), nullable=False),
        sa.Column('creation_date', sa.DateTime(), nullable=True),
        sa.Column('modification_date', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('aid')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP TABLE IF EXISTS installation_structs')
    op.execute('DROP TABLE IF EXISTS action_logs')
    ### end Alembic commands ###
