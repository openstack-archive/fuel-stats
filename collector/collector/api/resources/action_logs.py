from flask import request
from flask_jsonschema import validate as validate_request
from sqlalchemy import and_

from collector.api.app import app
from collector.api.app import db
from collector.api.db.model import ActionLogs
from collector.api.common.util import db_transaction
from collector.api.common.util import handle_response


@app.route('/api/v1/action_logs/', methods=['POST'])
@validate_request('action_logs', 'post_request')
@handle_response(201, 'action_logs', 'post_response')
@db_transaction
def post():
    app.logger.debug("Handling action_logs post request: {}".format(request.json))
    action_logs = request.json['action_logs']
    app.logger.debug("Inserting {} action logs".format(len(action_logs)))
    for action_log in action_logs:
        is_exists = db.session.query(ActionLogs).filter(and_(
            ActionLogs.node_aid == action_log['node_aid'],
            ActionLogs.external_id == action_log['external_id'],
        )).first()
        if is_exists is None:
            db.session.add(ActionLogs(**action_log))
    return {'status': 'ok'}
