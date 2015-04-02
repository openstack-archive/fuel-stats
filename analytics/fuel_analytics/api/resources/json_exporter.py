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
from flask import Response
from itertools import imap
import json
import six
from sqlalchemy import and_

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import InstallationStructure as IS
from fuel_analytics.api.db.model import OpenStackWorkloadStats as OSWL

bp = Blueprint('dto', __name__)


def row_as_dict(row):
    result = {}
    for column in row.__table__.columns:
        result[column.name] = six.text_type(getattr(row, column.name))
    return result


@bp.route('/installation_info/<master_node_uid>', methods=['GET'])
def get_installation_info(master_node_uid):
    app.logger.debug("Fetching installation info for: %s", master_node_uid)
    result = db.session.query(IS).filter(
        IS.master_node_uid == master_node_uid).one()
    dict_result = row_as_dict(result)
    app.logger.debug("Installation info for: %s fetched", master_node_uid)
    return Response(json.dumps(dict_result), mimetype='application/json')


def _get_oswls(sql_clauses, order_by=(OSWL.id.asc())):
    """Gets oswls by sql_clauses
    :param sql_clauses: collection of clauses for selecting oswls
    :return: generator on jsonyfied oswls data
    """
    result = db.session.query(OSWL).filter(and_(*sql_clauses)).order_by(
        order_by).all()
    dicts_result = imap(json.dumps, imap(row_as_dict, result))
    return dicts_result


@bp.route('/oswls/<master_node_uid>', methods=['GET'])
def get_oswls(master_node_uid):
    app.logger.debug("Fetching oswl info for: %s", master_node_uid)
    sql_clauses = (OSWL.master_node_uid == master_node_uid,)
    oswls_data = _get_oswls(sql_clauses)
    app.logger.debug("Oswl info for: %s fetched", master_node_uid)
    return Response(oswls_data, mimetype='application/json')


@bp.route('/oswls/<master_node_uid>/<resource_type>', methods=['GET'])
def get_oswls_by_resource_type(master_node_uid, resource_type):
    app.logger.debug("Fetching oswl info for: %s, %s",
                     master_node_uid, resource_type)
    sql_clauses = (OSWL.master_node_uid == master_node_uid,
                   OSWL.resource_type == resource_type)
    oswls_data = _get_oswls(sql_clauses)
    app.logger.debug("Oswl info for: %s, %s fetched",
                     master_node_uid, resource_type)
    return Response(oswls_data, mimetype='application/json')
