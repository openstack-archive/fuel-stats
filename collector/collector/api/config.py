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

import logging
import os

import six


class Production(object):
    DEBUG = False
    VALIDATE_RESPONSE = False
    LOG_FILE = '/var/log/fuel-stats/collector.log'
    LOG_LEVEL = logging.ERROR
    LOG_ROTATION = False
    LOGGER_NAME = 'collector'
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://collector:*****@localhost/collector'
    # If you need to filter releases please fill FILTERING_RULES.
    # Filtration is performed by release and build_id from installation
    # info fuel_release data.
    #
    # Structure of FILTERING_RULES for releases < 8.0:
    #   {release: {build_id: from_dt}}
    # Structure of FILTERING_RULES for releases >= 8.0:
    #   {release: {('fuel-nailgun-8.0.0-1.mos8212.noarch',
    #               'fuel-library8.0-8.0.0-1.mos7718.noarch'): from_dt}}
    #
    # PAY ATTENTION: you must use tuples as indexes in the FILTERING_RULES
    #
    # If packages and build_id are set simultaneously both conditions
    # will be checked. Installation info will be filtered if any of build_id
    # or packages filtered.
    #
    # Example of FILTERING_RULES:
    # {'6.1':
    #    {
    #        # 6.1 build 2015-04-13_234_13-12-31 became not filtered only
    #        # after 2015-04-30T23:00:18 UTC
    #        '2015-04-13_234_13-12-31': '2015-04-30T23:00:18',
    #
    #        # 6.1 build 2015-04-13_06-18-10 not filtered
    #        '2015-04-13_06-18-10': None
    #  },
    #  '6.1.1': {},  # All builds of 6.1.1 filtered
    #  '7.0': None,   # All builds of 7.0 not filtered
    #  '8.0': [{'packages_list': ['fuel-nailgun-8.0.0-1.mos8212.noarch'],
    #           'from_date': '2016-02-01T23:00:18'},
    #          {'packages_list': ['fuel-nailgun-8.0.0-2.mos9345.noarch']},
    #          {'build_id': 'build_id_value', 'from_date': '2016-03-01'},
    #          {'build_id': 'build_id_value'}]
    # }
    #
    # If you don't need any filtration, please set FILTERING_RULES = None
    # or FILTERING_RULES = {}
    FILTERING_RULES = None


class Testing(Production):
    DEBUG = True
    VALIDATE_RESPONSE = True
    LOG_FILE = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'test', 'logs', 'collector.log'))
    LOG_LEVEL = logging.DEBUG
    LOG_ROTATION = True
    LOG_FILE_SIZE = 2048000
    LOG_FILES_COUNT = 5
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://collector:collector@localhost/collector'
    SQLALCHEMY_ECHO = True


def packages_as_index(packages):
    if isinstance(packages, (list, tuple)):
        return tuple(sorted(packages))
    else:
        return packages


def convert_rules_to_dict(rules):
    """Converts filtering rules for release to internal format

    :param rules: dict or list of filtering rules for the release
    :return: dict of converted filtering rules
    """

    # Already converted or doesn't need to be converted
    if isinstance(rules, dict):
        return rules

    # If rules is list of dicts
    result = {}
    for rule in rules:
        if 'packages_list' in rule:
            build_info = packages_as_index(rule['packages_list'])
        else:
            build_info = rule['build_id']

        result[build_info] = rule.get('from_date')

    return result


def index_filtering_rules(app):
    """Rebuilds packages based keys in FILTERING_RULES.

    For accurate search we need to have sorted packages tuples as indexes
    in the FILTERING_RULES.

    :param app: Flask application
    """

    filtering_rules = app.config.get('FILTERING_RULES')

    if not filtering_rules:
        return

    for release, rules in six.iteritems(filtering_rules):
        if not rules:
            continue
        filtering_rules[release] = convert_rules_to_dict(rules)
