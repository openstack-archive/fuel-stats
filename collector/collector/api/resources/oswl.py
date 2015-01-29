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
from flask import json
from flask import request
from flask_jsonschema import validate as validate_request
import six
from sqlalchemy import and_
from sqlalchemy import or_

bp = Blueprint('oswl', __name__)

from collector.api.app import app
from collector.api.app import db
from collector.api.common import consts
from collector.api.common import util
from collector.api.common.util import db_transaction
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response
from collector.api.db.model import ActionLog, OpenStackWorkloadStats


@bp.route('/', methods=['POST'])
@validate_request('oswl', 'request')
@handle_response('oswl', 'response')
@exec_time
def post():
    app.logger.debug(
        "Handling oswl post request: %s", request.json
    )
    oswls = request.json['oswls']
    app.logger.debug("Saving %d oswls", len(oswls))
    oswls_resp = []
    for oswl in oswls:
        oswls_resp.append(_save_oswl(oswl))

    # objects_info = []
    # for chunk in util.split_collection(action_logs, chunk_size=1000):
    #     existed_objs, action_logs_to_add = _separate_action_logs(chunk)
    #     objects_info.extend(_extract_objects_info(existed_objs))
    #     skipped_objs = []
    #     for obj in action_logs_to_add:
    #         if obj['body']['action_type'] == 'nailgun_task' and \
    #                 not obj['body']['end_timestamp']:
    #             skipped_objs.append(obj)
    #         else:
    #             obj['body'] = json.dumps(obj['body'])
    #     for obj in skipped_objs:
    #         action_logs_to_add.remove(obj)
    #     objects_info.extend(_extract_dicts_info(
    #         skipped_objs, consts.ACTION_LOG_STATUSES.failed))
    #     objects_info.extend(_save_action_logs(action_logs_to_add))
    return 200, {'status': 'ok', 'oswls': oswls_resp}


@db_transaction
def _save_oswl(oswl):
    d = dict(oswl)
    d['external_id'] = d.pop('id')
    mn_uid = d['master_node_uid']
    external_id = d['external_id']
    app.logger.debug("Saving oswl master_node_uid: %s, external_id: %s",
                     mn_uid, external_id)
    response = {
        'master_node_uid': mn_uid,
        'id':  external_id
    }
    try:
        clauses = (
            OpenStackWorkloadStats.master_node_uid == mn_uid,
            OpenStackWorkloadStats.external_id == external_id
        )
        obj = db.session.query(OpenStackWorkloadStats).filter(and_(*clauses)).first()
        if obj:
            obj.update(**d)
            response['status'] = consts.OSWL_STATUSES.existed
        else:
            obj = OpenStackWorkloadStats(**d)
            response['status'] = consts.OSWL_STATUSES.added
        db.session.add(obj)
        db.session.flush()
    except Exception:
        response['status'] = consts.OSWL_STATUSES.failed
    app.logger.debug("Oswl master_node_uid: %s, external_id: %s saved. "
                     "Response: %s", mn_uid, external_id, response)
    return response

#
# @db_transaction
# def _save_action_logs(action_logs):
#     result = []
#     if not action_logs:
#         return result
#     try:
#         db.session.execute(ActionLog.__table__.insert(), action_logs)
#         result = _extract_dicts_info(
#             action_logs, consts.ACTION_LOG_STATUSES.added)
#     except Exception:
#         app.logger.exception("Processing of action logs chunk failed")
#         result = _extract_dicts_info(
#             action_logs, consts.ACTION_LOG_STATUSES.failed)
#     return result
#
#
# def _extract_objects_info(objects):
#     result = []
#     for obj in objects:
#         result.append({
#             'master_node_uid': obj.master_node_uid,
#             'external_id': obj.external_id,
#             'status': consts.ACTION_LOG_STATUSES.existed
#         })
#     return result
#
#
# def _extract_dicts_info(dicts, status):
#     result = []
#     for action_log in dicts:
#         result.append({
#             'master_node_uid': action_log['master_node_uid'],
#             'external_id': action_log['external_id'],
#             'status': status
#         })
#     return result
#
#
# def _separate_action_logs(action_logs):
#     existed_objs = []
#     action_logs_idx = \
#         util.build_index(action_logs, 'master_node_uid', 'external_id')
#     clauses = []
#     for master_node_uid, ext_id in six.iterkeys(action_logs_idx):
#         clauses.append(and_(
#             ActionLog.master_node_uid == master_node_uid,
#             ActionLog.external_id == ext_id
#         ))
#     found_objs = db.session.query(ActionLog).filter(or_(*clauses)).all()
#
#     for existed in found_objs:
#         existed_objs.append(existed)
#         idx = (existed.master_node_uid, existed.external_id)
#         action_logs_idx.pop(idx)
#     return existed_objs, list(six.itervalues(action_logs_idx))
