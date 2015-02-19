#    Copyright 2015 Mirantis, Inc.
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

"""OSWL stats DB structure

Revision ID: 4da2da15ec42
Revises: 558f628a238
Create Date: 2015-01-27 17:41:50.594143

"""

# revision identifiers, used by Alembic.
revision = '4da2da15ec42'
down_revision = '558f628a238'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


resource_type = sa.Enum('vm', 'tenant', 'volume', 'security_group',
                        'keystone_user', 'flavor', 'cluster_stats',
                        name='oswl_resource_type')


def upgrade():
    op.create_table(
        'oswl_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_node_uid', sa.Text(), nullable=False),
        sa.Column('external_id', sa.Integer(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('created_date', sa.Date(), nullable=False),
        sa.Column('updated_time', sa.Time(), nullable=False),
        sa.Column('resource_type', resource_type, nullable=False),
        sa.Column('resource_data', postgresql.JSON(), nullable=True),
        sa.Column('resource_checksum', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('master_node_uid', 'external_id', 'resource_type')
    ),
    op.create_index(op.f('ix_oswl_stats_created_date'), 'oswl_stats',
                    ['created_date'], unique=False)
    op.create_index(op.f('ix_oswl_stats_external_id'), 'oswl_stats',
                    ['external_id'], unique=False)
    op.create_index(op.f('ix_oswl_stats_master_node_uid'), 'oswl_stats',
                    ['master_node_uid'], unique=False)
    op.create_index(op.f('ix_oswl_stats_resource_type'), 'oswl_stats',
                    ['resource_type'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_oswl_stats_resource_type'),
                  table_name='oswl_stats')
    op.drop_index(op.f('ix_oswl_stats_master_node_uid'),
                  table_name='oswl_stats')
    op.drop_index(op.f('ix_oswl_stats_external_id'),
                  table_name='oswl_stats')
    op.drop_index(op.f('ix_oswl_stats_created_date'),
                  table_name='oswl_stats')
    op.drop_table('oswl_stats')
    resource_type.drop(bind=op.get_bind(), checkfirst=False)
    ### end Alembic commands ###
