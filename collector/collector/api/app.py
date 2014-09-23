import flask
import flask_jsonschema
import flask_sqlalchemy
import os


app = flask.Flask(__name__)

# Extensions
app.config['JSONSCHEMA_DIR'] = os.path.join(app.root_path, 'schemas')
flask_jsonschema.JsonSchema(app)
db = flask_sqlalchemy.SQLAlchemy(app, session_options={'autocommit': True})

# Errors handling
from collector.api import error_handling

# Resources handling
from collector.api.resources import action_logs

