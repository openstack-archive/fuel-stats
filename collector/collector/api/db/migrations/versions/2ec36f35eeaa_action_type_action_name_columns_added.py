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

"""action_type action_name columns added to action_logs

Revision ID: 2ec36f35eeaa
Revises: 4f46e2c07565
Create Date: 2016-02-03 15:52:13.397631

"""

# action_type and action_name columns added to action_logs
revision = '2ec36f35eeaa'
down_revision = '4f46e2c07565'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('action_logs', sa.Column('action_name', sa.Text(),
                                           nullable=True))
    op.add_column('action_logs', sa.Column('action_type', sa.Text(),
                                           nullable=True))
    op.create_index(op.f('ix_action_logs_action_name_action_type'),
                    'action_logs', ['action_name', 'action_type'],
                    unique=False)

    set_action_name = sa.sql.text(
        "UPDATE action_logs "
        "SET action_name = body->'action_name'::TEXT"
    )
    set_action_type = sa.sql.text(
        "UPDATE action_logs "
        "SET action_type = body->'action_type'::TEXT"
    )
    connection = op.get_bind()
    connection.execute(set_action_name)
    connection.execute(set_action_type)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_action_logs_action_name_action_type'),
                  table_name='action_logs')
    op.drop_column('action_logs', 'action_type')
    op.drop_column('action_logs', 'action_name')
    ### end Alembic commands ###
