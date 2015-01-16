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
from fuel_analytics.api.resources.utils.es_client import EsClient
from fuel_analytics.api.resources.utils.stats_to_csv import StatsToCsv

bp = Blueprint('csv_exporter', __name__)


@bp.route('/clusters', methods=['GET'])
def csv_exporter():
    app.logger.debug("Handling csv_exporter get request")
    es_client = EsClient()
    structures = es_client.get_structures()

    exporter = StatsToCsv()
    result = exporter.export_clusters(structures)

    # NOTE: result - is generator, but streaming can not work with some
    # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
    return Response(result, mimetype='text/csv')
