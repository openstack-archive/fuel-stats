from flask import request
from flask_jsonschema import validate as validate_request

from collector.api.app import app
from collector.api.app import db
from collector.api.db.model import ActionLogs
from collector.api.common.util import handle_response


@app.route('/api/v1/action_logs/', methods=['POST'])
@validate_request('action_logs', 'post_request')
@handle_response(201, 'action_logs', 'post_response')
def post():
    app.logger.debug("Handling action_logs post request: {}".format(request.json))
    action_logs = request.json['action_logs']
    app.logger.debug("Inserting {} action logs".format(len(action_logs)))
    if action_logs:
        db.session.begin()
        db.session.execute(
            ActionLogs.__table__.insert(),
            action_logs
        )
        db.session.commit()
    return {'status': 'ok'}
