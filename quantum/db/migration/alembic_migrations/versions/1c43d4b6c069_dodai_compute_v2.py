# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 OpenStack Foundation
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
#

"""description of revision

Revision ID: 1c43d4b6c069
Revises: grizzly
Create Date: 2013-07-19 15:39:55.370556

"""

# revision identifiers, used by Alembic.
revision = '1c43d4b6c069'
down_revision = 'grizzly'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'quantum.plugins.dodai.dodai_plugin.DodaiL2EPlugin'
]

from alembic import op
import sqlalchemy as sa


from quantum.db import migration


def upgrade(active_plugin=None, options=None):
    if not migration.should_run(active_plugin, migration_for_plugins):
        return

    op.create_table(
        'externalnetworks',
        sa.Column('network_id', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('network_id')
    )
    op.create_table(
        'floatingips',
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('floating_ip_address', sa.String(length=64), nullable=False),
        sa.Column('floating_network_id', sa.String(length=36), nullable=False),
        sa.Column('floating_port_id', sa.String(length=36), nullable=False),
        sa.Column('fixed_port_id', sa.String(length=36), nullable=True),
        sa.Column('fixed_ip_address', sa.String(length=64), nullable=True),
        sa.Column('router_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['floating_port_id'], ['ports.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fixed_port_id'], ['ports.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'dodai_networks',
        sa.Column('network_id', sa.String(length=36), nullable=False),
        sa.Column('vlan_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('network_id')
    )
    op.create_table(
        'dodai_outer_ports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dpid', sa.String(length=255), nullable=True),
        sa.Column('outer_port', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade(active_plugin=None, options=None):
    if not migration.should_run(active_plugin, migration_for_plugins):
        return

    op.drop_table('externalnetworks')
    op.drop_table('floatingips')
    op.drop_table('dodai_networks')
    op.drop_table('dodai_outer_ports')
