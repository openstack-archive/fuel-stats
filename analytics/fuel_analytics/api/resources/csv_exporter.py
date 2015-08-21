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
import io
import six
import tarfile

from flask import Blueprint
from flask import request
from flask import Response
from sqlalchemy import distinct
from sqlalchemy import or_
from sqlalchemy import sql

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import InstallationStructure as IS
from fuel_analytics.api.db.model import OpenStackWorkloadStats as OSWS
from fuel_analytics.api.errors import DateExtractionError
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv

bp = Blueprint('clusters_to_csv', __name__)

CLUSTERS_REPORT_FILE = 'clusters.csv'
PLUGINS_REPORT_FILE = 'plugins.csv'


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
    """Composes query for fetching not filtered installation
    structures info with filtering by from and to dates and
    ordering by id. Installation structure is not filtered
    if is_filtered is False or None.
    :param from_date: filter from creation or modification date
    :param to_date: filter to creation or modification date
    :return: SQLAlchemy query
    """
    query = db.session.query(IS)
    query = query.filter(or_(
        IS.is_filtered == bool(False),  # workaround for PEP8 error E712
        IS.is_filtered.is_(None)))
    if from_date is not None:
        query = query.filter(or_(IS.creation_date >= from_date,
                                 IS.modification_date >= from_date))
    if to_date is not None:
        # modification_date is datetime field, so we need to
        # increase to_date for right filtering
        to_date += timedelta(days=1)
        query = query.filter(or_(IS.creation_date <= to_date,
                                 IS.modification_date <= to_date))
    return query.order_by(IS.id)


def get_inst_structures():
    yield_per = app.config['CSV_DB_YIELD_PER']
    from_date = get_from_date()
    to_date = get_to_date()
    return get_inst_structures_query(from_date=from_date,
                                     to_date=to_date).yield_per(yield_per)


def get_action_logs():
    from_date = get_from_date()
    to_date = get_to_date()
    # Selecting only last network verification task for master node cluster
    query = "SELECT DISTINCT ON (master_node_uid, body->>'cluster_id') " \
            "external_id, master_node_uid, body->'cluster_id' cluster_id, " \
            "body->'additional_info'->'ended_with_status' status, " \
            "to_timestamp(body->>'end_timestamp', 'YYYY-MM-DD')::TIMESTAMP " \
            "WITHOUT TIME ZONE end_timestamp, " \
            "body->>'action_name' action_name " \
            "FROM action_logs " \
            "WHERE body->>'action_type'='nailgun_task' " \
            "AND body->>'action_name'='verify_networks' " \
            "AND to_timestamp(body->>'end_timestamp', 'YYYY-MM-DD')::" \
            "TIMESTAMP WITHOUT TIME ZONE >= :from_date " \
            "AND to_timestamp(body->>'end_timestamp', 'YYYY-MM-DD')::" \
            "TIMESTAMP WITHOUT TIME ZONE <= :to_date " \
            "ORDER BY master_node_uid, body->>'cluster_id', external_id DESC"
    return db.session.execute(
        sql.text(query), {'from_date': from_date, 'to_date': to_date})


@bp.route('/clusters', methods=['GET'])
def clusters_to_csv():
    app.logger.debug("Handling clusters_to_csv get request")
    inst_structures = get_inst_structures()
    action_logs = get_action_logs()
    exporter = StatsToCsv()
    result = exporter.export_clusters(inst_structures, action_logs)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Get request for clusters_to_csv handled")
    headers = {
        'Content-Disposition': 'attachment; filename={}'.format(
            CLUSTERS_REPORT_FILE)
    }
    return Response(result, mimetype='text/csv', headers=headers)


@bp.route('/plugins', methods=['GET'])
def plugins_to_csv():
    app.logger.debug("Handling plugins_to_csv get request")
    inst_structures = get_inst_structures()
    exporter = StatsToCsv()
    result = exporter.export_plugins(inst_structures)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Get request for plugins_to_csv handled")
    headers = {
        'Content-Disposition': 'attachment; filename={}'.format(
            PLUGINS_REPORT_FILE)
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
        OSWS.id, OSWS.master_node_uid, OSWS.cluster_id,
        OSWS.created_date,  # for checking if row is duplicated in CSV
        OSWS.created_date.label('stats_on_date'),  # for showing in CSV
        OSWS.resource_type, OSWS.resource_data,
        IS.creation_date.label('installation_created_date'),
        IS.modification_date.label('installation_updated_date'),
        IS.structure['fuel_release'].label('fuel_release'),
        IS.is_filtered).\
        join(IS, IS.master_node_uid == OSWS.master_node_uid).\
        filter(OSWS.resource_type == resource_type).\
        filter(or_(IS.is_filtered == bool(False), IS.is_filtered.is_(None)))
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
    result = exporter.export(resource_type, oswls, get_to_date())

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Request oswl_to_csv for resource %s handled",
                     resource_type)
    headers = {
        'Content-Disposition': 'attachment; filename={}.csv'.format(
            resource_type)
    }
    return Response(result, mimetype='text/csv', headers=headers)


def get_resources_types():
    """Gets all available resource types
    :return: generator of resources types names collection
    """
    result = db.session.query(distinct(OSWS.resource_type))
    return (row[0] for row in result)


def get_all_reports_generators():
    """Returns reports generators
    :return type: list of tuples (report generator, report name)
    """
    app.logger.debug("Creating all reports generators")
    reports_generators = []
    stats_exporter = StatsToCsv()
    oswl_exporter = OswlStatsToCsv()

    app.logger.debug("Creating installation structures report generator")
    inst_strucutres = get_inst_structures()
    action_logs = get_action_logs()
    clusters = stats_exporter.export_clusters(inst_strucutres, action_logs)
    reports_generators.append((clusters, CLUSTERS_REPORT_FILE))
    app.logger.debug("Installation structures report generator created")

    app.logger.debug("Creating plugins report generator")
    plugins = stats_exporter.export_plugins(inst_strucutres)
    reports_generators.append((plugins, PLUGINS_REPORT_FILE))
    app.logger.debug("Plugins report generator created")

    resources_types = get_resources_types()

    for resource_type in resources_types:
        app.logger.debug("Getting resource generator '%s'", resource_type)

        oswls = get_oswls(resource_type)
        resources = oswl_exporter.export(
            resource_type, oswls, get_to_date())
        reports_generators.append((resources, '{}.csv'.format(resource_type)))
        app.logger.debug("Report generator '%s' got", resource_type)

    app.logger.debug("All reports generators created")

    return reports_generators


def stream_reports(reports_generators):
    app.logger.debug("Streaming reports as archive started")
    tar_stream = six.StringIO()
    with tarfile.open(None, mode='w', fileobj=tar_stream) as f:
        for report_generator, report_name in reports_generators:
            app.logger.debug("Streaming report %s", report_name)
            stream = six.StringIO()
            info = tarfile.TarInfo(report_name)
            for row in report_generator:
                stream.write(row)
            info.size = stream.tell()
            stream.seek(io.SEEK_SET)
            f.addfile(info, stream)

            tar_stream.seek(io.SEEK_SET)
            yield tar_stream.getvalue()

            tar_stream.seek(io.SEEK_SET)
            tar_stream.truncate()

    app.logger.debug("Streaming reports as archive finished")


@bp.route('/all', methods=['GET'])
def all_reports_stream():
    """Single report for all resource types, clusters and plugins info
    :return: tar archive of CSV reports
    """
    app.logger.debug("Handling all_reports get request")
    reports_generators = get_all_reports_generators()

    name = 'reports_from{}_to{}'.format(get_from_date(), get_to_date())
    headers = {
        'Content-Disposition': 'attachment; filename={}.tar'.format(name)
    }
    return Response(stream_reports(reports_generators),
                    mimetype='application/x-tar', headers=headers)
