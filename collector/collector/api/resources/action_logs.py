from flask import jsonify
from flask import request
from flask_jsonschema import validate as validate_request

from collector.api.app import app
from collector.api.common.util import handle_response


@app.route('/api/v1/action_logs/', methods=['POST'])
@validate_request('action_logs', 'post_request')
@handle_response(201, 'action_logs', 'post_response')
def post():
    app.logger.debug("action_logs post request: {}".format(request.json))
    return {'status': 'ok'}


@app.route('/api/v1/action_logs/', methods=['GET'])
def get():
    return jsonify({'get': 'ok'}), 200
