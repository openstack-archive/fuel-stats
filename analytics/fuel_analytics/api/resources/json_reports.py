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
import sqlalchemy

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db

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
    """Extracts and aggregates installation and environments info

    We have list of clusters in the DB field installations_info.structure.
    The cluster data stored as dict. Unfortunately we have no ways in the
    DB layer to extract only required fields from the dicts in the list.
    For decrease memory consumption we are selecting only required fields
    from clusters data.

    For instance we want to extract only statuses of the clusters:
    {"clusters": [{"status": "error", ...}, {"status": "new", ...},
    {"status": "operational", ...}].

    The only way to fetch only required data is expanding of cluster data to
    separate rows in the SQL query result and extract only required fields.
    For this purpose we are selecting FROM installation_structures,
    json_array_elements(...).

    Unfortunately rows with empty clusters list wouldn't be in the output.
    As workaround we are adding empty cluster data in this case [{}].
    Also we have ordering or rows by id.

    Now we able to select only required fields in rows and rows are ordered
    by id. So clusters are grouped by the installation id. When we are
    iterating other the clusters the changing of id is marker of changing
    installation.

    :param release: filter data by Fuel release
    :return: aggregated installations and environments info
    """

    params = {'is_filtered': False}
    # For counting installations without clusters we are
    # adding empty cluster data into SQL result: [{}]
    query = "SELECT id, release, " \
            "cluster_data->>'status' status, " \
            "structure->>'clusters_num' clusters_num, " \
            "cluster_data->>'nodes_num' nodes_num, " \
            "cluster_data->'attributes'->>'libvirt_type' hypervisor, " \
            "cluster_data->'release'->>'os' os_name " \
            "FROM installation_structures, " \
            "json_array_elements(CASE " \
            "  WHEN structure->>'clusters' = '[]' THEN '[{}]' " \
            "  ELSE structure->'clusters' " \
            "  END" \
            ") AS cluster_data " \
            "WHERE is_filtered = :is_filtered"
    if release:
        params['release'] = release
        query += " AND release = :release"
    query += " ORDER BY id"
    query = sqlalchemy.text(query)

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

    last_id = None
    for row in db.session.execute(query, params):

        extract_installation_info(row, info[release], last_id)
        cur_release = row[1]

        # Splitting info by release if fetching for all releases
        if not release and cur_release != release:
            extract_installation_info(row, info[cur_release], last_id)

        last_id = row[0]

    app.logger.debug("Fetched installations info from DB for release: "
                     "%s, info: %s", release, info)
    return info


def extract_installation_info(row, result, last_id):
    """Extracts installation info from structure

    :param row: row with data from DB
    :type row: tuple
    :param result: placeholder for extracted data
    :type result: dict
    :param last_id: DB id of last processed installation
    :param last_id: int
    """

    (cur_id, cur_release, status, clusters_num, nodes_num,
     hypervisor, os_name) = row

    inst_info = result['installations']
    env_info = result['environments']

    production_statuses = ('operational', 'error')

    if last_id != cur_id:
        inst_info['count'] += 1
        inst_info['environments_num'][clusters_num] += 1

    # For empty clusters data we don't increase environments count
    try:
        if int(clusters_num):
            env_info['count'] += 1
    except (ValueError, TypeError):
        app.logger.exception("Value of clusters_num %s "
                             "can't be casted to int", clusters_num)

    if status in production_statuses:
        if nodes_num:
            env_info['nodes_num'][nodes_num] += 1
            env_info['operable_envs_count'] += 1

        if hypervisor:
            env_info['hypervisors_num'][hypervisor.lower()] += 1

        if os_name:
            env_info['oses_num'][os_name.lower()] += 1

    if status is not None:
        env_info['statuses'][status] += 1
