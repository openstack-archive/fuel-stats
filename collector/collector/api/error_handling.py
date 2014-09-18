from flask import jsonify
from flask import make_response
import flask_jsonschema

from collector.api.app import app


@app.errorhandler(400)
def bad_request(error):
    app.logger.error("Bad request: {}".format(error))
    return make_response(jsonify({'status': 'error', 'message': '{}'.format(error)}), 400)


@app.errorhandler(404)
def not_found(error):
    app.logger.error("Not found: {}".format(error))
    return make_response(jsonify({'status': 'error', 'message': '{}'.format(error)}), 404)


@app.errorhandler(flask_jsonschema.ValidationError)
def validation_error(error):
    app.logger.error("Validation error: {}".format(error))
    return make_response(jsonify({'status': 'error', 'message': '{}'.format(error)}), 400)


@app.errorhandler(500)
def server_error(error):
    app.logger.error("Server error: {}".format(error))
    return make_response(jsonify({'status': 'error', 'message': '{0}: {1}'.format(error.__class__.__name__, error)}), 500)





