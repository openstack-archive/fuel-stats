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

from collections import namedtuple


def make_enum(*values, **kwargs):
    names = kwargs.get('names')
    if names:
        return namedtuple('Enum', names)(*values)
    return namedtuple('Enum', values)(*values)


ITEMS_STATUSES = make_enum(
    'added',
    'existed',
    'failed'
)


ACTION_LOG_STATUSES = ITEMS_STATUSES


OSWL_STATUSES = ITEMS_STATUSES


OSWL_RESOURCE_TYPES = make_enum(
    'vm',
    'tenant',
    'volume',
    'security_group',
    'keystone_user',
    'flavor',
    'cluster_stats'
)