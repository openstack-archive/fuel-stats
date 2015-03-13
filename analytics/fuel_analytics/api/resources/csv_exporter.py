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
from flask import send_file
import os
import shutil
from sqlalchemy import distinct
from sqlalchemy import or_
from sqlalchemy import sql
import tempfile
import zipfile

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


def get_action_logs_query(from_date, to_date):
    """Selecting only last network verification task for master node cluster
    :param from_date: filter from creation or modification date
    :param to_date: filter to creation or modification date
    :return: SQLAlchemy query
    """
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


def get_action_logs():
    from_date = get_from_date()
    to_date = get_to_date()
    return get_action_logs_query(from_date, to_date)


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
        'Content-Disposition': 'attachment; filename=clusters.csv'
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
        'Content-Disposition': 'attachment; filename=plugins.csv'
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


def save_all_reports(tmp_dir):
    """Saves all available CSV reports into single directory
    :param tmp_dir: path to target directory
    """
    app.logger.debug("Saving all reports to %s", tmp_dir)
    stats_exporter = StatsToCsv()
    oswl_exporter = OswlStatsToCsv()

    resources_types = get_resources_types()
    inst_strucutres = get_inst_structures()
    with open(os.path.join(tmp_dir, 'clusters.csv'), mode='w') as f:
        app.logger.debug("Getting installation structures started")
        action_logs = get_action_logs()
        clusters = stats_exporter.export_clusters(inst_strucutres,
                                                  action_logs)
        f.writelines(clusters)
        app.logger.debug("Getting installation structures finished")

    with open(os.path.join(tmp_dir, 'plugins.csv'), mode='w') as f:
        app.logger.debug("Getting plugins started")
        plugins = stats_exporter.export_plugins(inst_strucutres)
        f.writelines(plugins)
        app.logger.debug("Getting plugins finished")

    for resource_type in resources_types:
        app.logger.debug("Getting resource '%s' started", resource_type)

        file_name = os.path.join(tmp_dir, '{}.csv'.format(resource_type))
        oswls = get_oswls(resource_type)
        with open(file_name, mode='w') as f:
            resources = oswl_exporter.export(
                resource_type, oswls, get_to_date())
            f.writelines(resources)
        app.logger.debug("Getting resource '%s' finished", resource_type)
    app.logger.debug("All reports saved into %s", tmp_dir)


def archive_dir(dir_path):
    """Archives directory to zip file
    :param dir_path: path to target directory
    :return: ZipFile object
    """
    app.logger.debug("Dir '%s' archiving started", dir_path)
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(dir_path):
            for f in files:
                archive.write(os.path.join(root, f), arcname=f)
        app.logger.debug("Dir '%s' archiving to '%s' finished",
                         dir_path, archive.filename)
        return archive


@bp.route('/all', methods=['GET'])
def all_reports():
    """Single report for all resource types and clusters info
    :return: zip archive of CSV reports
    """
    app.logger.debug("Handling all_reports get request")
    tmp_dir = tempfile.mkdtemp()
    try:
        save_all_reports(tmp_dir)
        try:
            archive = archive_dir(tmp_dir)
            name = 'reports_from{}_to{}.zip'.format(
                get_from_date(), get_to_date())
            return send_file(archive.filename, mimetype='application/zip',
                             as_attachment=True, attachment_filename=name)
        finally:
            app.logger.debug("Removing temporary archive")
            os.unlink(archive.filename)
    finally:
        app.logger.debug("Removing temporary directory %s", tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        app.logger.debug("Request all_reports handled")
