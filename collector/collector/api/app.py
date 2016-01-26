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

from flask import Flask
from flask import jsonify
from flask import make_response
import flask_jsonschema
import flask_sqlalchemy
import os
from sqlalchemy.exc import IntegrityError

from collector.api.config import index_filtering_rules


app = Flask(__name__)


# Registering flask extensions
app.config['JSONSCHEMA_DIR'] = os.path.join(app.root_path, 'schemas')
flask_jsonschema.JsonSchema(app)

# We should rebuild packages based keys in the FILTERING_RULES.
# Sorted tuples built from packages lists are used as keys.
index_filtering_rules(app)

db = flask_sqlalchemy.SQLAlchemy(app)


# Registering blueprints
from collector.api.resources.action_logs import bp as action_logs_bp
from collector.api.resources.installation_structure import \
    bp as installation_structure_bp
from collector.api.resources.oswl import bp as oswl_stats_bp
from collector.api.resources.ping import bp as ping_bp

app.register_blueprint(installation_structure_bp,
                       url_prefix='/api/v1/installation_structure')
app.register_blueprint(action_logs_bp, url_prefix='/api/v1/action_logs')
app.register_blueprint(ping_bp, url_prefix='/api/v1/ping')
app.register_blueprint(oswl_stats_bp, url_prefix='/api/v1/oswl_stats')


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
