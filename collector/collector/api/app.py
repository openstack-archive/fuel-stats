from flask import Flask
from flask import jsonify
from flask import make_response
import flask_jsonschema
import flask_sqlalchemy
import os
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)


# Registering flask extensions
app.config['JSONSCHEMA_DIR'] = os.path.join(app.root_path, 'schemas')
flask_jsonschema.JsonSchema(app)

db = flask_sqlalchemy.SQLAlchemy(app, session_options={'autocommit': True})


# Registering blueprints
from collector.api.resources.action_logs import bp as action_logs_bp
from collector.api.resources.ping import bp as ping_bp

app.register_blueprint(action_logs_bp)
app.register_blueprint(ping_bp)


# Registering error handlers
@app.errorhandler(400)
def bad_request(error):
    app.logger.error("Bad request: {}".format(error))
    return make_response(jsonify({'status': 'error',
                                  'message': '{}'.format(error)}), 400)


@app.errorhandler(IntegrityError)
def integrity_error(error):
    app.logger.error("Bad request: {}".format(error))
    return make_response(jsonify({'status': 'error',
                                  'message': '{}'.format(error)}), 400)


@app.errorhandler(404)
def not_found(error):
    app.logger.error("Not found: {}".format(error))
    return make_response(jsonify({'status': 'error',
                                  'message': '{}'.format(error)}), 404)


@app.errorhandler(405)
def not_allowed(error):
    app.logger.error("Method not allowed: {}".format(error))
    return make_response(jsonify({'status': 'error',
                                  'message': '{}'.format(error)}), 405)


@app.errorhandler(flask_jsonschema.ValidationError)
def validation_error(error):
    app.logger.error("Validation error: {}".format(error))
    return make_response(jsonify({'status': 'error',
                                  'message': '{}'.format(error)}), 400)


@app.errorhandler(500)
def server_error(error):
    app.logger.error("Server error: {}".format(error))
    error_name = error.__class__.__name__
    return make_response(
        jsonify(
            {
                'status': 'error',
                'message': '{0}: {1}'.format(error_name, error)
            }
        ),
        500
    )
