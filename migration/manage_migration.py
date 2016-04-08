#!/usr/bin/env python

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

import argparse
import six
import yaml

from migration.test.test_env import configure_test_env


def handle_mode(params):
    if params.mode == 'test':
        configure_test_env()


def handle_external_config(params):
    if params.config:
        with open(params.config) as f:
            from migration import config

            content = yaml.load(f)
            if isinstance(content, dict):
                for k, v in six.iteritems(content):
                    setattr(config, k, v)


def execute(params):
    handle_mode(params)
    handle_external_config(params)
    # importing Migrator only after test or prod environment is configured
    from migration.migrator import Migrator
    migrator = Migrator()
    if params.action == 'migrate':
        # We don't use action logs in the Elasticsearch reports.
        # Action logs table contains huge number of action logs,
        # thus we are temporary comment this migration.
        # TODO (akislitsky): uncomment this when ActionLogs
        # reports will be introduced into Fuel stats web UI.
        # migrator.migrate_action_logs()
        migrator.migrate_installation_structure()
    elif params.action == 'remove_indices':
        migrator.remove_indices()
    elif params.action == 'create_indices':
        migrator.create_indices()
    elif params.action == 'clear_indices':
        migrator.remove_indices()
        migrator.create_indices()


def load_action_parser(subparsers):
    subparsers.add_parser('migrate', help="Migrate statistics from PostgreSql to Elasticsearch")
    subparsers.add_parser('remove_indices', help="Remove statistics indices from Elasticsearch")
    subparsers.add_parser('create_indices', help="Create statistics indices in Elasticsearch")
    subparsers.add_parser('clear_indices', help="Remove and create statistics indices in Elasticsearch")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m', '--mode',
        help="Running mode",
        choices=('test', 'prod'),
        default='prod'
    )
    parser.add_argument(
        '-c', '--config',
        help="Path to additional yaml config file"
    )

    subparsers = parser.add_subparsers(
        dest='action',
        help="Action to be executed"
    )
    load_action_parser(subparsers)

    params = parser.parse_args()
    execute(params)
