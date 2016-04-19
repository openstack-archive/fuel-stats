# Copyright 2015 Mirantis, Inc.
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

import csv
import io
import itertools

import six
from sqlalchemy.util import KeyedTuple

from fuel_analytics.api.app import app


def get_keys_paths(skeleton):
    """Gets paths to leaf keys in the data
    :param skeleton: data skeleton
    :return: list of lists of dict keys
    """
    def _keys_paths_helper(keys, skel):
        result = []

        if isinstance(skel, dict):
            for k in sorted(six.iterkeys(skel)):
                result.extend(_keys_paths_helper(keys + [k], skel[k]))
        elif isinstance(skel, (list, tuple)):
            # For lists in the skeleton we can specify repeats value.
            # For instance we want to show 3 roles in the CSV report.
            # In this case skeleton for roles will be {'roles': [None, 3]}
            if len(skel) > 1:
                repeats = skel[1]
            else:
                repeats = app.config['CSV_DEFAULT_LIST_ITEMS_NUM']

            if len(skel):
                for idx in six.moves.xrange(repeats):
                    result.extend(_keys_paths_helper(keys + [idx], skel[0]))
            else:
                result.append(keys)

        elif hasattr(skel, '__call__'):
            # Handling aggregate functions in the skeleton. For instance if
            # we want to show number of networks we will have the following
            # skeleton: {'networks': count}
            result.append(keys + [skel])
        else:
            result.append(keys)
        return result
    return _keys_paths_helper([], skeleton)


def get_flatten_data(keys_paths, data):
    """Creates flatten data from data by keys_paths

    :param keys_paths: list of dict keys lists
    :param data: dict with nested structures
    :return: list of flatten data dicts
    """
    flatten_data = []
    for key_path in keys_paths:
        d = data
        for key in key_path:
            if hasattr(key, '__call__'):
                # Handling aggregate functions in the skeleton
                d = key(d)
                break
            if isinstance(d, dict):
                d = d.get(key, None)
            elif isinstance(d, KeyedTuple):
                # If we specify DB fields in the query SQLAlchemy
                # returns KeyedTuple inherited from tuple
                d = getattr(d, key, None)
            elif isinstance(d, (list, tuple)):
                d = d[key] if key < len(d) else None
            else:
                d = getattr(d, key, None)
            if d is None:
                break
        if isinstance(d, (list, tuple)):
            # If type for list items is not specified values
            # will be shown as joined text
            flatten_data.append(' '.join(map(six.text_type, d)))
        else:
            flatten_data.append(d)
    return flatten_data


def construct_skeleton(data):
    """Creates structure for searching all key paths in given data
    :param data: fetched from ES dict
    :return: skeleton of data structure
    """
    if isinstance(data, dict):
        result = {}
        for k in sorted(data.keys()):
            result[k] = construct_skeleton(data[k])
        return result
    elif isinstance(data, (list, tuple)):
        list_result = []
        dict_result = {}
        for d in data:
            if isinstance(d, dict):
                dict_result.update(construct_skeleton(d))
            elif isinstance(d, (list, tuple)):
                if not list_result:
                    list_result.append(construct_skeleton(d))
                else:
                    list_result[0].extend(construct_skeleton(d))
        if dict_result:
            list_result.append(dict_result)
        return list_result
    else:
        return None


def get_data_skeleton(structures):
    """Constructs and merges skeletons from raw data

    :param structures: list of data
    :return: skeleton for provided data structures
    """
    def _merge_skeletons(lh, rh):
        keys_paths = get_keys_paths(rh)
        for keys_path in keys_paths:
            merge_point = lh
            data_point = rh
            for key in keys_path:
                data_point = data_point[key]
                if isinstance(data_point, dict):
                    if key not in merge_point:
                        merge_point[key] = {}
                elif isinstance(data_point, (list, tuple)):
                    if key not in merge_point:
                        merge_point[key] = [get_data_skeleton(data_point)]
                    else:
                        _merge_skeletons(merge_point[key][0],
                                         get_data_skeleton(data_point))
                    break
                else:
                    merge_point[key] = None
                merge_point = merge_point[key]

    skeleton = {}
    for structure in structures:
        app.logger.debug("Constructing skeleton by data: %s", structure)
        new_skeleton = construct_skeleton(structure)
        app.logger.debug("Updating skeleton by %s", new_skeleton)
        _merge_skeletons(skeleton, new_skeleton)
        app.logger.debug("Result skeleton is %s", skeleton)
    return skeleton


def flatten_data_as_csv(keys_paths, flatten_data):
    """Returns flatten data in CSV
    :param keys_paths: list of dict keys lists for columns names
    generation
    :param flatten_data: list of flatten data dicts
    :return: stream with data in CSV format
    """
    app.logger.debug("Saving flatten data as CSV started")
    names = []
    for key_path in keys_paths:
        # Handling functions and list indexes in key_path
        key_texts = (getattr(k, '__name__', six.text_type(k))
                     for k in key_path)
        names.append('.'.join(key_texts))

    output = six.BytesIO()
    writer = csv.writer(output)

    def read_and_flush():
        output.seek(io.SEEK_SET)
        data = output.read()
        output.seek(io.SEEK_SET)
        output.truncate()
        return data

    for d in itertools.chain((names,), flatten_data):
        encoded_d = [s.encode("utf-8") if isinstance(s, unicode) else s
                     for s in d]
        writer.writerow(encoded_d)
        yield read_and_flush()
    app.logger.debug("Saving flatten data as CSV finished")


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
