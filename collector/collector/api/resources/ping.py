#    Copyright 2014 Mirantis, Inc.
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
from flask_jsonschema import validate as validate_request

from collector.api.app import app
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response


bp = Blueprint('ping', __name__, url_prefix='/api/v1/ping')


@bp.route('/', methods=['GET'])
@validate_request('ping', 'request')
@handle_response(200, 'ping', 'response')
@exec_time
def ping():
    app.logger.debug("Handling ping get request: {}".format(request.json))
    return {'status': 'ok'}
