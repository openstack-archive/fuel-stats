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

import datetime
from flask import current_app
from flask import jsonify
from functools import wraps
import jsonschema
import math

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
            current_app.logger.debug(
                "Processing response: {}".format(response)
            )
            if current_app.config.get('VALIDATE_RESPONSE', False) and path:
                current_app.logger.debug(
                    "Validating response: {}".format(response)
                )
                jsonschema_ext = current_app.extensions.get('jsonschema')
                jsonschema.validate(response, jsonschema_ext.get_schema(path))
                current_app.logger.debug(
                    "Response validated: {}".format(response)
                )
            current_app.logger.debug(
                "Response processed: {}".format(response)
            )
            return jsonify(response), http_code
        return decorated
    return wrapper


def exec_time(fn):
    """Adds 'exec_time' into function result dict. Execution time is
    in seconds with microseconds. Decorator should be applied
    after handle_response (before response is jsonified) and before
    db_transaction (to take account of DB transaction processing).
    """
    @wraps(fn)
    def decorated(*args, **kwargs):
        start = datetime.datetime.now()
        resp = fn(*args, **kwargs)
        end = datetime.datetime.now()
        td = end - start
        resp['exec_time'] = float('%d.%06d' % (td.seconds, td.microseconds))
        return resp
    return decorated


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
        except Exception:
            db.session.rollback()
            raise
    return decorated


def split_collection(collection, chunk_size=1000):
    chunks_num = int(math.ceil(float(len(collection)) / chunk_size))
    for i in xrange(chunks_num):
        start = i * chunk_size
        end = start + chunk_size
        yield collection[start:end]


def build_index(dicts_coll, *fields):
    index = {}
    for d in dicts_coll:
        idx = tuple([d[f] for f in fields])
        index[idx] = d
    return index
