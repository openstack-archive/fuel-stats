from flask import request
from flask_jsonschema import validate as validate_request

from collector.api.app import app
from collector.api.common.util import exec_time
from collector.api.common.util import handle_response


@app.route('/api/v1/ping/', methods=['GET'])
@validate_request('ping', 'request')
@handle_response(200, 'ping', 'response')
@exec_time
def ping():
    app.logger.debug("Handling ping get request: {}".format(request.json))
    return {'status': 'ok'}
