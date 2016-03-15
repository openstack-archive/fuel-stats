#    Copyright 2016 Mirantis, Inc.
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

"""Data versioning table added

Revision ID: 2807015d1fa6
Revises: 2ec36f35eeaa
Create Date: 2016-03-11 18:09:57.875275

"""

# revision identifiers, used by Alembic.
revision = '2807015d1fa6'
down_revision = '2ec36f35eeaa'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('version_tag', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), server_default='NOW',
                  nullable=False),
        sa.Column('data_diff', postgresql.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_history_created'), 'history',
                    ['created'], unique=False)
    op.create_index(op.f('ix_history_resource_id'), 'history',
                    ['resource_id'], unique=False)
    op.create_index(op.f('ix_history_resource_type'), 'history',
                    ['resource_type'], unique=False)
    op.create_index(op.f('ix_history_version_tag'), 'history',
                    ['version_tag'], unique=False)

    op.execute('CREATE SEQUENCE history_version_tag_seq')

    op.create_table(
        'history_last_snapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), server_default='NOW',
                  nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_history_last_snapshot_created'),
                    'history_last_snapshot', ['created'], unique=False)
    op.create_index(op.f('ix_history_last_snapshot_resource_id'),
                    'history_last_snapshot', ['resource_id'], unique=False)
    op.create_index(op.f('ix_history_last_snapshot_resource_type'),
                    'history_last_snapshot', ['resource_type'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_history_last_snapshot_resource_type'),
                  table_name='history_last_snapshot')
    op.drop_index(op.f('ix_history_last_snapshot_resource_id'),
                  table_name='history_last_snapshot')
    op.drop_index(op.f('ix_history_last_snapshot_created'),
                  table_name='history_last_snapshot')
    op.drop_table('history_last_snapshot')

    op.execute('DROP SEQUENCE history_version_tag_seq')

    op.drop_index(op.f('ix_history_version_tag'), table_name='history')
    op.drop_index(op.f('ix_history_resource_type'), table_name='history')
    op.drop_index(op.f('ix_history_resource_id'), table_name='history')
    op.drop_index(op.f('ix_history_created'), table_name='history')
    op.drop_table('history')
    ### end Alembic commands ###
