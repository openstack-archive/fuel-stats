from flask import current_app
from flask import jsonify
from functools import wraps
import jsonschema

from collector.api.app import db


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
            current_app.logger.debug("Processing response: {}".format(response))
            if current_app.config.get('VALIDATE_RESPONSE', False) and path:
                current_app.logger.debug("Validating response: {}".format(response))
                jsonschema_ext = current_app.extensions.get('jsonschema')
                jsonschema.validate(response, jsonschema_ext.get_schema(path))
                current_app.logger.debug("Response validated: {}".format(response))
            current_app.logger.debug("Response processed: {}".format(response))
            return jsonify(response), http_code
        return decorated
    return wrapper


def exec_time():
    pass


def db_transaction(fn):
    """Wraps function call into DB transaction
    """
    @wraps(fn)
    def decorated(*args, **kwargs):
        db.session.begin()
        try:
            result = fn(*args, **kwargs)
            db.session.commit()
            return result
        except:
            db.session.rollback()
            raise
    return decorated
