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

from datetime import datetime
from datetime import timedelta
from flask import Blueprint
from flask import request
from flask import Response
from sqlalchemy import or_

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import InstallationStructure as IS
from fuel_analytics.api.db.model import OpenStackWorkloadStats as OSWS
from fuel_analytics.api.errors import DateExtractionError
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv

bp = Blueprint('clusters_to_csv', __name__)


def extract_date(field_name, default_value=None, date_format='%Y-%m-%d'):
    if field_name not in request.args:
        return default_value
    date_string = request.args.get(field_name, default_value)
    try:
        result = datetime.strptime(date_string, date_format).date()
        app.logger.debug("Extracted '{}' value {}".format(field_name, result))
        return result
    except ValueError:
        msg = "Date '{}' value in wrong format. Use format: {}".format(
            field_name, date_format)
        app.logger.debug(msg)
        raise DateExtractionError(msg)


def get_from_date():
    default_value = datetime.utcnow().date() - \
        timedelta(days=app.config.get('CSV_DEFAULT_FROM_DATE_DAYS'))
    return extract_date('from_date', default_value=default_value)


def get_to_date():
    return extract_date('to_date',
                        default_value=datetime.utcnow().date())


def get_inst_structures_query(from_date=None, to_date=None):
    """Composes query for fetching installation structures
    info with filtering by from and to dates and ordering by id
    :param from_date: filter from creation or modification date
    :param to_date: filter to creation or modification date
    :return: SQLAlchemy query
    """
    query = db.session.query(IS)
    if from_date is not None:
        query = query.filter(or_(IS.creation_date >= from_date,
                                 IS.modification_date >= from_date))
    if to_date is not None:
        query = query.filter(or_(IS.creation_date <= to_date,
                                 IS.modification_date <= to_date))
    return query.order_by(IS.id)


def get_inst_structures():
    yield_per = app.config['CSV_DB_YIELD_PER']
    from_date = get_from_date()
    to_date = get_to_date()
    return get_inst_structures_query(from_date=from_date,
                                     to_date=to_date).yield_per(yield_per)


@bp.route('/clusters', methods=['GET'])
def clusters_to_csv():
    app.logger.debug("Handling clusters_to_csv get request")
    inst_structures = get_inst_structures()
    exporter = StatsToCsv()
    result = exporter.export_clusters(inst_structures)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Get request for clusters_to_csv handled")
    headers = {
        'Content-Disposition': 'attachment; filename=clusters.csv'
    }
    return Response(result, mimetype='text/csv', headers=headers)


def get_oswls_query(resource_type, from_date=None, to_date=None):
    """Composes query for fetching oswls with installation
    info creation and update dates with ordering by created_date
    :param resource_type: resource type
    :param from_date: filter from date
    :param to_date: filter to date
    :return: SQLAlchemy query
    """
    query = db.session.query(
        OSWS.master_node_uid, OSWS.cluster_id,
        OSWS.created_date,  # for checking if row is duplicated in CSV
        OSWS.created_date.label('stats_on_date'),  # for showing in CSV
        OSWS.resource_type, OSWS.resource_data,
        IS.creation_date.label('installation_created_date'),
        IS.modification_date.label('installation_updated_date')).\
        join(IS, IS.master_node_uid == OSWS.master_node_uid).\
        filter(OSWS.resource_type == resource_type)
    if from_date is not None:
        query = query.filter(OSWS.created_date >= from_date)
    if to_date is not None:
        query = query.filter(OSWS.created_date <= to_date)
    return query.order_by(OSWS.created_date)


def get_oswls(resource_type):
    yield_per = app.config['CSV_DB_YIELD_PER']
    app.logger.debug("Fetching %s oswls with yeld per %d",
                     resource_type, yield_per)
    from_date = get_from_date()
    to_date = get_to_date()
    return get_oswls_query(resource_type, from_date=from_date,
                           to_date=to_date).yield_per(yield_per)


@bp.route('/<resource_type>', methods=['GET'])
def oswl_to_csv(resource_type):
    app.logger.debug("Handling oswl_to_csv get request for resource %s",
                     resource_type)

    exporter = OswlStatsToCsv()
    oswls = get_oswls(resource_type)
    result = exporter.export(resource_type, oswls)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Request oswl_to_csv for resource %s handled",
                     resource_type)
    headers = {
        'Content-Disposition': 'attachment; filename={}.csv'.format(
            resource_type)
    }
    return Response(result, mimetype='text/csv', headers=headers)
