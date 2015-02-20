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

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.db.model import InstallationStructure as IS
from fuel_analytics.api.db.model import OpenStackWorkloadStats as OSWS
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv

bp = Blueprint('clusters_to_csv', __name__)


def get_inst_structures(yield_per=1000):
    return db.session.query(IS).order_by(IS.id).yield_per(yield_per)


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


def get_oswls_query(resource_type):
    return db.session.query(
        OSWS.master_node_uid, OSWS.cluster_id, OSWS.created_date,
        OSWS.updated_time, OSWS.resource_type, OSWS.resource_data,
        IS.creation_date.label('installation_created_date'),
        IS.modification_date.label('installation_updated_date')).\
        join(IS, IS.master_node_uid == OSWS.master_node_uid).\
        filter(OSWS.resource_type == resource_type).\
        order_by(OSWS.created_date)


def get_oswls(resource_type, yield_per=1000):
    app.logger.debug("Fetching %s oswls with yeld per %d",
                     resource_type, yield_per)
    return get_oswls_query(resource_type).yield_per(yield_per)


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
