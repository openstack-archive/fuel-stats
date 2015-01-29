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

from datetime import datetime
from flask import Blueprint
from flask import json
from flask import request
from flask_jsonschema import validate as validate_request

bp = Blueprint('installation_structure', __name__)

from collector.api.app import app
from collector.api.app import db
from collector.api.common.util import db_transaction
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response
from collector.api.db.model import InstallationStructure


@bp.route('/', methods=['POST'])
@validate_request('installation_structure', 'request')
@handle_response('installation_structure', 'response')
@db_transaction
@exec_time
def post():
    app.logger.debug(
        "Handling installation_structure post request: {}".format(request.json)
    )
    structure = request.json['installation_structure']
    master_node_uid = structure['master_node_uid']
    obj = db.session.query(InstallationStructure).filter(
        InstallationStructure.master_node_uid == master_node_uid).first()
    if obj is None:
        app.logger.debug("Saving new structure")
        obj = InstallationStructure(master_node_uid=master_node_uid)
        obj.creation_date = datetime.utcnow()
        status_code = 201
    else:
        app.logger.debug("Updating structure {}".format(obj.id))
        obj.modification_date = datetime.utcnow()
        status_code = 200
    obj.structure = json.dumps(structure)
    db.session.add(obj)
    return status_code, {'status': 'ok'}
