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

from fuel_analytics.api.app import app

bp = Blueprint('dto', __name__)


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

# @bp.route('/clusters', methods=['GET'])
# def clusters_to_csv():
#     app.logger.debug("Handling clusters_to_csv get request")
#     inst_structures = get_inst_structures()
#     action_logs = get_action_logs()
#     exporter = StatsToCsv()
#     result = exporter.export_clusters(inst_structures, action_logs)
#
#     # NOTE: result - is generator, but streaming can not work with some
#     # WSGI middlewares: http://flask.pocoo.org/docs/0.10/patterns/streaming/
#     app.logger.debug("Get request for clusters_to_csv handled")
#     headers = {
#         'Content-Disposition': 'attachment; filename={}'.format(
#             CLUSTERS_REPORT_FILE)
#     }
#     return Response(result, mimetype='text/csv', headers=headers)
#
