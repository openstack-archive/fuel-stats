from flask import request
from flask_jsonschema import validate as validate_request
from sqlalchemy import and_
from sqlalchemy import or_

from collector.api.app import app
from collector.api.app import db
from collector.api.db.model import ActionLog
from collector.api.common import consts
from collector.api.common import util
from collector.api.common.util import db_transaction
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response


@app.route('/api/v1/action_logs/', methods=['POST'])
@validate_request('action_logs', 'request')
@handle_response(201, 'action_logs', 'response')
@exec_time
def post():
    app.logger.debug("Handling action_logs post request: {}".format(request.json))
    action_logs = request.json['action_logs']
    app.logger.debug("Inserting {} action logs".format(len(action_logs)))
    objects_info = []
    for chunk in util.split_collection(action_logs, chunk_size=1000):
        existed_objs, action_logs_to_add = _separate_action_logs(chunk)
        _handle_existed_objects(objects_info, existed_objs)
        _save_action_logs(objects_info, action_logs_to_add)
    return {'status': 'ok', 'action_logs': list(objects_info)}


@db_transaction
def _save_action_logs(objects_info, action_logs):
    if not action_logs:
        return
    try:
        db.session.execute(ActionLog.__table__.insert(), action_logs)
        for action_log in action_logs:
            objects_info.append({
                'node_aid': action_log['node_aid'],
                'external_id': action_log['external_id'],
                'status': consts.ACTION_LOG_STATUSES.added
            })
    except:
        app.logger.exception("Processing of action logs chunk failed")
        _handle_chunk_processing_error(objects_info, action_logs)


def _handle_existed_objects(objects_info, existed_objects):
    for obj in existed_objects:
        objects_info.append({
            'node_aid': obj.node_aid,
            'external_id': obj.external_id,
            'status': consts.ACTION_LOG_STATUSES.existed
        })


def _handle_chunk_processing_error(objects_info, chunk):
    for action_log in chunk:
        objects_info.append({
            'node_aid': action_log['node_aid'],
            'external_id': action_log['external_id'],
            'status': consts.ACTION_LOG_STATUSES.failed
        })


def _separate_action_logs(action_logs):
    existed_objs = []
    action_logs_idx = util.build_index(action_logs, 'node_aid', 'external_id')
    clauses = []
    for aid, ext_id in action_logs_idx.keys():
        clauses.append(and_(ActionLog.node_aid == aid, ActionLog.external_id == ext_id))
    found_objs = db.session.query(ActionLog).filter(or_(*clauses)).all()

    for existed in found_objs:
        existed_objs.append(existed)
        idx = (existed.node_aid, existed.external_id)
        action_logs_idx.pop(idx)
    return existed_objs, action_logs_idx.values()
