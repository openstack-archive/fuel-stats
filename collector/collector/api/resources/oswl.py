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

bp = Blueprint('oswl_stats', __name__)

from collector.api.app import app
from collector.api.app import db
from collector.api.common import consts
from collector.api.common import util
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response
from collector.api.db.model import OpenStackWorkloadStats


@bp.route('/', methods=['POST'])
@validate_request('oswl', 'request')
@handle_response('oswl', 'response')
@exec_time
def post():
    app.logger.debug("Handling oswl post request: %s", request.json)
    oswls = request.json['oswl_stats']
    oswls_resp = []
    dict_idx_names = ('master_node_uid', 'id')
    obj_idx_names = ('master_node_uid', 'external_id')
    dict_to_obj_fields_mapping = zip(dict_idx_names, obj_idx_names)

    for chunk in util.split_collection(oswls):
        app.logger.debug("Processing oswls chunk of size: %d", len(chunk))
        dicts_new, objs_updated = \
            util.split_new_dicts_and_updated_objs(
                chunk, dict_to_obj_fields_mapping, OpenStackWorkloadStats)

        try:
            app.logger.debug("Bulk insert of oswls started")
            util.bulk_insert(dicts_new, OpenStackWorkloadStats)
            app.logger.debug("Bulk insert of oswls finished")
            db.session.commit()
            oswls_resp.extend(generate_success_response(dicts_new,
                                                        objs_updated))
            app.logger.debug("Oswls chunk of size: %d is processed",
                             len(chunk))
        except Exception:
            app.logger.exception("Oswls chunk of size: %d processing failed",
                                 len(chunk))
            db.session.rollback()
            oswls_resp.extend(generate_error_response(dicts_new,
                                                      objs_updated))
    return 200, {'status': 'ok', 'oswl_stats': oswls_resp}


def generate_success_response(dicts_new, objs_updated):
    oswls_resp = []
    for d in dicts_new:
        oswls_resp.append({
            'master_node_uid': d['master_node_uid'],
            'id': d['external_id'],
            'status': consts.OSWL_STATUSES.added
        })
    for o in objs_updated:
        oswls_resp.append({
            'master_node_uid': o.master_node_uid,
            'id': o.external_id,
            'status': consts.OSWL_STATUSES.updated
        })
    return oswls_resp


def generate_error_response(dicts_new, objs_updated):
    oswls_resp = []
    for d in dicts_new:
        oswls_resp.append({
            'master_node_uid': d['master_node_uid'],
            'id': d['external_id'],
            'status': consts.OSWL_STATUSES.failed
        })
    for o in objs_updated:
        oswls_resp.append({
            'master_node_uid': o.master_node_uid,
            'id': o.external_id,
            'status': consts.OSWL_STATUSES.failed
        })
    return oswls_resp
