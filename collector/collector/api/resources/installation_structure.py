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
from dateutil import parser
from flask import Blueprint
from flask import request
from flask_jsonschema import validate as validate_request

bp = Blueprint('installation_structure', __name__)

from collector.api.app import app
from collector.api.app import db
from collector.api.common.util import db_transaction
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response
from collector.api.config import normalize_build_info
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
    obj.is_filtered = _is_filtered(structure)
    obj.structure = structure
    db.session.add(obj)
    return status_code, {'status': 'ok'}


def _is_filtered_by_build_info(build_info, filtering_rules):
    """Calculates is build_info should be filtered or not.

    :param build_info: build_id or packages from the
                       installation info structure
    :param filtering_rules: filtering rules for release
    """

    # We don't have 'build_id' in structure since release 8.0
    # and 'packages' before 8.0
    if build_info is None:
        return False

    build_info = normalize_build_info(build_info)

    # build info not found
    if build_info not in filtering_rules:
        return True

    build_rules = filtering_rules.get(build_info)

    # No from_dt specified
    if build_rules is None:
        return False

    # from_dt in the past
    from_dt = parser.parse(build_rules)
    cur_dt = datetime.utcnow()
    if from_dt <= cur_dt:
        return False

    return True


def _is_filtered(structure):
    """Checks is structure should be filtered or not.
    For filtering uses rules defined at app.config['FILTERING_RULES']
    :param structure: dict with installation info structure data
    :return: bool
    """
    rules = app.config.get('FILTERING_RULES')
    # No rules specified
    if not rules:
        return False

    # Extracting data from structure
    fuel_release = structure.get('fuel_release', {})
    release = fuel_release.get('release')
    build_id = fuel_release.get('build_id')
    packages = structure.get('fuel_packages')

    # Release not in rules
    if release not in rules:
        return True

    filtering_rules = rules.get(release)

    # Filtering rules doesn't specified
    if filtering_rules is None:
        return False

    filtered_by_build_id = _is_filtered_by_build_info(
        build_id, filtering_rules)

    filtered_by_packages = _is_filtered_by_build_info(
        packages, filtering_rules)

    return filtered_by_build_id or filtered_by_packages
