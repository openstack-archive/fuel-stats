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

from collections import defaultdict
import copy
import json

from flask import Blueprint
from flask import request
from flask import Response
import memcache

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import InstallationStructure as IS

bp = Blueprint('reports', __name__)


@bp.route('/installations', methods=['GET'])
def get_installations_info():
    release = request.args.get('release')
    refresh = request.args.get('refresh')
    cache_key_prefix = 'fuel-stats-installations-info'
    mc = memcache.Client(app.config.get('MEMCACHED_HOSTS'))
    app.logger.debug("Fetching installations info for release: %s", release)

    # Checking cache
    if not refresh:
        cache_key = '{0}{1}'.format(cache_key_prefix, release)
        app.logger.debug("Checking installations info by key: %s in cache",
                         cache_key)
        cached_result = mc.get(cache_key)
        if cached_result:
            app.logger.debug("Installations info cache found by key: %s",
                             cache_key)
            return Response(cached_result, mimetype='application/json')
        else:
            app.logger.debug("No cached installations info for key: %s",
                             cache_key)
    else:
        app.logger.debug("Enforce refresh cache of installations info "
                         "for release: %s", release)

    # Fetching data from DB
    info_from_db = get_installations_info_from_db(release)

    # Saving fetched data to cache
    for for_release, info in info_from_db.items():
        cache_key = '{0}{1}'.format(cache_key_prefix, for_release)
        app.logger.debug("Caching installations info for key: %s, data: %s",
                         cache_key, info)
        mc.set(cache_key, json.dumps(info),
               app.config.get('MEMCACHED_JSON_REPORTS_EXPIRATION'))

    return Response(json.dumps(info_from_db[release]),
                    mimetype='application/json')


def get_installations_info_from_db(release):
    query = db.session.query(IS.structure, IS.release).\
        filter(IS.is_filtered == bool(0))
    if release:
        query = query.filter(IS.release == release)

    info_template = {
        'installations': {
            'count': 0,
            'environments_num': defaultdict(int)
        },
        'environments': {
            'count': 0,
            'operable_envs_count': 0,
            'statuses': defaultdict(int),
            'nodes_num': defaultdict(int),
            'hypervisors_num': defaultdict(int),
            'oses_num': defaultdict(int)
        }
    }

    info = defaultdict(lambda: copy.deepcopy(info_template))

    app.logger.debug("Fetching installations info from DB for release: %s",
                     release)

    yield_per = app.config['JSON_DB_YIELD_PER']
    for row in query.yield_per(yield_per):
        structure = row[0]
        extract_installation_info(structure, info[release])

        cur_release = row[1]
        # Splitting info by release if fetching for all releases
        if not release and cur_release != release:
            extract_installation_info(structure, info[cur_release])

    app.logger.debug("Fetched installations info from DB for release: "
                     "%s, info: %s", release, info)

    return info


def extract_installation_info(source, result):
    """Extracts installation info from structure

    :param source: source of installation info data
    :type source: dict
    :param result: placeholder for extracted data
    :type result: dict
    """

    inst_info = result['installations']
    env_info = result['environments']

    production_statuses = ('operational', 'error')

    inst_info['count'] += 1
    envs_num = 0

    for cluster in source.get('clusters', []):
        envs_num += 1
        env_info['count'] += 1

        if cluster.get('status') in production_statuses:
            current_nodes_num = cluster.get('nodes_num', 0)
            env_info['nodes_num'][current_nodes_num] += 1
            env_info['operable_envs_count'] += 1

            hypervisor = cluster.get('attributes', {}).get('libvirt_type')
            if hypervisor:
                env_info['hypervisors_num'][hypervisor.lower()] += 1

            os = cluster.get('release', {}).get('os')
            if os:
                env_info['oses_num'][os.lower()] += 1

        status = cluster.get('status')
        if status is not None:
            env_info['statuses'][status] += 1

    inst_info['environments_num'][envs_num] += 1
