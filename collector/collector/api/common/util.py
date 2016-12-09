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
from six.moves import xrange
from sqlalchemy import and_
from sqlalchemy import or_

from collector.api.app import db


def handle_response(*path):
    """Checks response, if VALIDATE_RESPONSE in app.config is set to True
    and path is not empty.
    Jsonifies response, adds http_code to returning values.

    :param path: path to response json schema
    :type path: collection of strings
    :return: tuple of jsonifyed response and http_code
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            http_code, response = fn(*args, **kwargs)
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
        status_code, resp = fn(*args, **kwargs)
        end = datetime.datetime.now()
        td = end - start
        resp['exec_time'] = float('%d.%06d' % (td.seconds, td.microseconds))
        return status_code, resp
    return decorated


def db_transaction(fn):
    """Wraps function call into DB transaction
    """
    @wraps(fn)
    def decorated(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise
    return decorated


def split_collection(collection, chunk_size=1000):
    """Splits collection on chunks
    :param collection: input collection
    :param chunk_size: size of chunk
    :return:
    """
    chunks_num = int(math.ceil(float(len(collection)) / chunk_size))
    for i in xrange(chunks_num):
        start = i * chunk_size
        end = start + chunk_size
        yield collection[start:end]


def build_index(coll, *fields):
    """Builds dict from collection. Dict keys are built
    from values of fields of collection items
    :param coll: collection
    :param fields: fields names for build result dict key
    :return: dict of collection items indexed by attributes
    values of collection item from 'fields'
    """
    index = {}
    for d in coll:
        if isinstance(d, dict):
            idx = tuple(d[f] for f in fields)
        else:
            idx = tuple(getattr(d, f) for f in fields)
        index[idx] = d
    return index


def get_index(target, *fields):
    """Gets value of index for target object
    :param target: target object
    :param fields: fields names for index creation
    :return: tuple of attributes values of target from 'fields'
    """
    if isinstance(target, dict):
        return tuple(target[field_name] for field_name in fields)
    else:
        return tuple(getattr(target, field_name) for field_name in fields)


def get_existed_objects_query(dicts, dict_to_obj_fields_mapping, model_class):
    """Generates SQL query for filtering existed objects
    :param dicts: list of dicts
    :param dict_to_obj_fields_mapping: tuple of pairs
    ('dict_field_name', 'obj_field_name') used for filtering existed objects
    :param model_class: DB model
    :return: SQL query for filtering existed objects
    """
    dict_index_fields, obj_index_fields = zip(*dict_to_obj_fields_mapping)
    clauses = []
    for d in dicts:
        clause = []
        for idx, dict_field_name in enumerate(dict_index_fields):
            obj_field_name = obj_index_fields[idx]
            clause.append(
                getattr(model_class, obj_field_name) == d[dict_field_name]
            )
        clauses.append(and_(*clause))
    return db.session.query(model_class).filter(or_(*clauses))


def split_new_dicts_and_updated_objs(dicts, dict_to_obj_fields_mapping,
                                     model_class):
    """Separates new data and updates existed objects
    :param dicts: list of dicts for processing
    :param dict_to_obj_fields_mapping: tuple of pairs
    ('dict_field_name', 'obj_field_name') used for filtering existed objects
    :param model_class: DB model
    :return: list of dicts for new objects, list of updated existed objects
    """
    dict_index_fields, obj_index_fields = zip(*dict_to_obj_fields_mapping)

    # Fetching existed objects
    existed_objs = get_existed_objects_query(
        dicts, dict_to_obj_fields_mapping, model_class).all()
    existed_objs_idx = build_index(existed_objs, *obj_index_fields)

    new_dicts = []
    for d in dicts:
        obj_idx = get_index(d, *dict_index_fields)

        # Preparing data for saving. We should change field names as
        # described in dict_to_obj_fields_mapping
        d_copy = d.copy()
        for idx, dict_field in enumerate(dict_index_fields):
            obj_field = obj_index_fields[idx]
            d_copy[obj_field] = d_copy.pop(dict_field)

        if obj_idx in existed_objs_idx:
            # Updating existed object
            obj = existed_objs_idx[obj_idx]
            for k, v in d_copy.items():
                setattr(obj, k, v)
        else:
            new_dicts.append(d_copy)
    return new_dicts, existed_objs


def bulk_insert(dicts, model_class):
    if dicts:
        db.session.execute(model_class.__table__.insert(dicts))
