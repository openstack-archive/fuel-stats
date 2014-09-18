import flask
import flask_jsonschema
import os


app = flask.Flask(__name__)
app.config['JSONSCHEMA_DIR'] = os.path.join(app.root_path, 'schemas')
flask_jsonschema.JsonSchema(app)

# Application errors handling
from collector.api import error_handling

# Application resources handling
from collector.api.resources import action_logs
