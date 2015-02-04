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
from fuel_analytics.api.common.consts import OSWL_RESOURCE_TYPES as RT
from fuel_analytics.api.db.model import OpenStackWorkloadStats
from fuel_analytics.api.resources.utils.es_client import ElasticSearchClient
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv

bp = Blueprint('clusters_to_csv', __name__)


@bp.route('/clusters', methods=['GET'])
def clusters_to_csv():
    app.logger.debug("Handling clusters_to_csv get request")
    es_client = ElasticSearchClient()
    structures = es_client.get_structures()

    exporter = StatsToCsv()
    result = exporter.export_clusters(structures)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Get request for clusters_to_csv handled")
    return Response(result, mimetype='text/csv')


def get_oswls(yield_per=1000):
    app.logger.debug("Fetching oswls with yeld per %d", yield_per)
    return db.session.query(OpenStackWorkloadStats).filter(
        OpenStackWorkloadStats.resource_type == RT.vm).yield_per(yield_per)


@bp.route('/vms', methods=['GET'])
def vms_to_csv():
    app.logger.debug("Handling vms_to_csv get request")
    oswls = get_oswls()

    exporter = OswlStatsToCsv()
    result = exporter.export_vms(oswls)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    app.logger.debug("Get request for vms_to_csv handled")
    return Response(result, mimetype='text/csv')
