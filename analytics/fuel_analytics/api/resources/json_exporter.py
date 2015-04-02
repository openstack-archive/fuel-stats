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

from flask import Blueprint
from flask import request
from flask import Response
import json
import six
from sqlalchemy import and_

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import ActionLog as AL
from fuel_analytics.api.db.model import InstallationStructure as IS
from fuel_analytics.api.db.model import OpenStackWorkloadStats as OSWL

bp = Blueprint('dto', __name__)


def row_as_dict(row):
    return {c.name: six.text_type(getattr(row, c.name))
            for c in row.__table__.columns}


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
    dict_result = row_as_dict(result)
    app.logger.debug("Installation info for: %s fetched", master_node_uid)
    return Response(json.dumps(dict_result), mimetype='application/json')


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
    return (row_as_dict(obj) for obj in result)


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


@bp.route('/oswls/<master_node_uid>', methods=['GET'])
def get_oswls(master_node_uid):
    paging_params = get_paging_params()
    app.logger.debug("Fetching oswl info for: %s, paging prams: %s",
                     master_node_uid, paging_params)
    sql_clauses = (OSWL.master_node_uid == master_node_uid,)
    oswls_data = _get_db_objs_data(OSWL, sql_clauses,
                                   (OSWL.id.asc(),), paging_params)
    jsons_data = _jsonify_collection(oswls_data)
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
    jsons_data = _jsonify_collection(oswls_data)
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
    jsons_data = _jsonify_collection(action_logs_data)
    app.logger.debug("Action_logs for: %s, paging params: %s fetched",
                     master_node_uid, paging_params)
    return Response(jsons_data, mimetype='application/json')
