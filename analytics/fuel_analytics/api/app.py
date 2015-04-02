#    Copyright 2015 Mirantis, Inc.
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
from flask import make_response
import flask_sqlalchemy
import six

from fuel_analytics.api.errors import DateExtractionError
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
db = flask_sqlalchemy.SQLAlchemy(app)

# Registering blueprints
from fuel_analytics.api.resources.csv_exporter import bp as csv_exporter_bp
from fuel_analytics.api.resources.json_exporter import bp as json_exporter_bp

app.register_blueprint(csv_exporter_bp, url_prefix='/api/v1/csv')
app.register_blueprint(json_exporter_bp, url_prefix='/api/v1/json')


@app.errorhandler(DateExtractionError)
def date_parsing_error(error):
    return make_response(six.text_type(error), 400)


@app.errorhandler(NoResultFound)
def db_object_not_found(error):
    return make_response(six.text_type(error), 404)
