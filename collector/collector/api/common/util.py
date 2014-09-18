from flask import current_app, jsonify
from functools import wraps
import jsonschema


def handle_response(http_code, *path):
    """Checks response, if VALIDATE_RESPONSE in app.config is set to True
    and path is not empty.
    Jsonifies response, adds http_code to returning values.

    :param http_code:
    :type http_code: integer
    :param path: path to response json schema
    :type path: collection of strings
    :return: tuple of jsonifyed response and http_code
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            response = fn(*args, **kwargs)
            print "### handle_response", response
            if current_app.config.get('VALIDATE_RESPONSE', False) and path:
                print "### validating response"
                jschema = current_app.extensions.get('jsonschema')
                jsonschema.validate(response, jschema.get_schema(path))
            return jsonify(response), http_code
        return decorated
    return wrapper
