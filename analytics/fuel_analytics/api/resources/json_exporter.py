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

import datetime
import json
from sqlalchemy import and_
from sqlalchemy import func

from flask import Blueprint
from flask import request
from flask import Response

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import ActionLog as AL
from fuel_analytics.api.db.model import InstallationStructure as IS
from fuel_analytics.api.db.model import OpenStackWorkloadStats as OSWL

bp = Blueprint('dto', __name__)


def row_as_serializable_dict(row):
    """Converts SqlAlchemy object to dict serializable to json
    :param row: SqlAlchemy object
    :return: dict serializable to json
    """
    result = {}
    for c in row.__table__.columns:
        name = c.name
        value = getattr(row, c.name)
        if isinstance(value, (datetime.datetime, datetime.date,
                              datetime.time)):
            value = value.isoformat()
        result[name] = value
    return result


def get_dict_param(name):
    params = request.args.get(name)
    if not isinstance(params, dict):
        params = {}
    return params


def get_paging_params():
    params = get_dict_param('paging_params')
    return {
        'limit': params.get('limit', app.config['JSON_DB_DEFAULT_LIMIT']),
        'offset': params.get('offset', 0)
    }


@bp.route('/installation_info/<master_node_uid>', methods=['GET'])
def get_installation_info(master_node_uid):
    app.logger.debug("Fetching installation info for: %s", master_node_uid)
    result = db.session.query(IS).filter(
        IS.master_node_uid == master_node_uid).one()
    dict_result = row_as_serializable_dict(result)
    app.logger.debug("Installation info for: %s fetched", master_node_uid)
    return Response(json.dumps(dict_result), mimetype='application/json')


def _get_db_objs_count(model, sql_clauses):
    return db.session.query(model).filter(and_(*sql_clauses)).count()


def _get_db_objs_data(model, sql_clauses, order_by, paging_params):
    """Gets DB objects by sql_clauses
    :param model: DB model
    :param sql_clauses: collection of clauses for selecting DB objects
    :param order_by: tuple of orderings for DB objects
    :param paging_params: dictionary with limit, offset values
    :return: generator on dicts of DB objects data
    """
    query = db.session.query(model).filter(and_(*sql_clauses))
    for order in order_by:
        query = query.order_by(order)
    result = query.limit(paging_params['limit']).\
        offset(paging_params['offset']).all()
    return (row_as_serializable_dict(obj) for obj in result)


def _jsonify_collection(collection_iter):
    """Jsonifyes collection. Used for streaming
     list of jsons into Flask application response
    :param collection_iter: iterator on input collection
    :return: generator on chunks of jsonifyed result
    """
    yield '['
    try:
        yield json.dumps(collection_iter.next())
        while True:
            d = collection_iter.next()
            yield ', {}'.format(json.dumps(d))
    except StopIteration:
        pass
    finally:
        yield ']'


def _jsonify_paged_collection(collection_iter, paging_params, total):

    page_info = paging_params.copy()
    page_info['total'] = total

    yield '{{"paging_params": {0}, "objs": '.format(json.dumps(page_info))
    for item in _jsonify_collection(collection_iter):
        yield item
    yield '}'


@bp.route('/oswls/<master_node_uid>', methods=['GET'])
def get_oswls(master_node_uid):
    paging_params = get_paging_params()
    app.logger.debug("Fetching oswl info for: %s, paging prams: %s",
                     master_node_uid, paging_params)
    sql_clauses = (OSWL.master_node_uid == master_node_uid,)
    oswls_data = _get_db_objs_data(OSWL, sql_clauses,
                                   (OSWL.id.asc(),), paging_params)
    oswls_count = _get_db_objs_count(OSWL, sql_clauses)
    jsons_data = _jsonify_paged_collection(oswls_data, paging_params,
                                           oswls_count)
    app.logger.debug("Oswl info for: %s, paging params: %s fetched",
                     master_node_uid, paging_params)
    return Response(jsons_data, mimetype='application/json')


@bp.route('/oswls/<master_node_uid>/<resource_type>', methods=['GET'])
def get_oswls_by_resource_type(master_node_uid, resource_type):
    paging_params = get_paging_params()
    app.logger.debug("Fetching oswl info for: %s, %s, paging params: %s",
                     master_node_uid, resource_type, paging_params)
    sql_clauses = (OSWL.master_node_uid == master_node_uid,
                   OSWL.resource_type == resource_type)
    oswls_data = _get_db_objs_data(
        OSWL, sql_clauses, (OSWL.id.asc(), OSWL.resource_type.asc()),
        paging_params)
    oswls_total = _get_db_objs_count(OSWL, sql_clauses)
    jsons_data = _jsonify_paged_collection(oswls_data, paging_params,
                                           oswls_total)
    app.logger.debug("Oswl info for: %s, %s, paging prams: %s fetched",
                     master_node_uid, resource_type, paging_params)
    return Response(jsons_data, mimetype='application/json')


@bp.route('/action_logs/<master_node_uid>', methods=['GET'])
def get_action_logs(master_node_uid):
    paging_params = get_paging_params()
    app.logger.debug("Fetching action_logs for: %s, paging params: %s",
                     master_node_uid, paging_params)
    sql_clauses = (AL.master_node_uid == master_node_uid,)
    action_logs_data = _get_db_objs_data(AL, sql_clauses,
                                         (AL.id.asc(),), paging_params)
    action_logs_total = _get_db_objs_count(AL, sql_clauses)
    jsons_data = _jsonify_paged_collection(action_logs_data, paging_params,
                                           action_logs_total)
    app.logger.debug("Action_logs for: %s, paging params: %s fetched",
                     master_node_uid, paging_params)
    return Response(jsons_data, mimetype='application/json')


@bp.route('/installation_infos/filtered', methods=['GET'])
def get_filtered_installation_infos():
    paging_params = get_paging_params()
    app.logger.debug("Fetching filtered installation_info, paging params: %s",
                     paging_params)
    sql_clauses = (IS.is_filtered == bool(1),)  # Workaround for PEP8 E712
    inst_infos = _get_db_objs_data(IS, sql_clauses, (IS.id.asc(),),
                                   paging_params)
    inst_infos_total = _get_db_objs_count(IS, sql_clauses)
    jsons_data = _jsonify_paged_collection(inst_infos, paging_params,
                                           inst_infos_total)
    app.logger.debug("Filtered installation_info: %s fetched", paging_params)
    return Response(jsons_data, mimetype='application/json')


@bp.route('/summary', methods=['GET'])
def get_db_summary():
    app.logger.debug("Getting db summary")
    summary = {}
    for model in (IS, AL, OSWL):
        count = db.session.query(model).count()
        summary[model.__tablename__] = {'total': count}

    # Counting filtered installation info
    filtered_summary = db.session.query(
        IS.is_filtered, func.count(IS.id)).group_by(IS.is_filtered).all()
    filtered_num = 0
    not_filtered_num = 0
    for is_filtered, count in filtered_summary:
        if is_filtered is False:
            not_filtered_num += count
        else:
            filtered_num += count
    summary[IS.__tablename__]['not_filtered'] = not_filtered_num
    summary[IS.__tablename__]['filtered'] = filtered_num

    app.logger.debug("Db summary got")
    return Response(json.dumps(summary), mimetype='application/json')
