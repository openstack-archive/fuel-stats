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
            if isinstance(d, dict):
                d = d.get(key, None)
            else:
                d = getattr(d, key, None)
            if d is None:
                break
        if isinstance(d, (list, tuple)):
            flatten_data.append(' '.join(d))
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
        return data


def get_data_skeleton(structures):
    """Gets skeleton by structures list
    :param structures:
    :return: data structure skeleton
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
                elif isinstance(data_point, list):
                    if key not in merge_point:
                        merge_point[key] = [{}]
                    _merge_skeletons(merge_point[key][0],
                                     get_data_skeleton(data_point))
                else:
                    merge_point[key] = None
                merge_point = merge_point[key]

    skeleton = {}
    for structure in structures:
        app.logger.debug("Constructing skeleton by data: %s", structure)
        app.logger.debug("Updating skeleton by %s",
                         construct_skeleton(structure))
        _merge_skeletons(skeleton, construct_skeleton(structure))
        app.logger.debug("Result skeleton is %s", skeleton)
    return skeleton


def align_enumerated_field_values(values, number):
    """Fills result list by the None values, if number is greater than
    values len. The first element of result is bool value
    len(values) > number
    :param values:
    :param number:
    :return: aligned list to 'number' + 1 length, filled by Nones on
    empty values positions and bool value on the first place. Bool value
    is True if len(values) > number
    """
    return ([len(values) > number] +
            (values + [None] * (number - len(values)))[:number])


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
        names.append('.'.join(key_path))

    output = six.BytesIO()
    writer = csv.writer(output)

    def read_and_flush():
        output.seek(io.SEEK_SET)
        data = output.read()
        output.seek(io.SEEK_SET)
        output.truncate()
        return data

    for d in itertools.chain((names,), flatten_data):
        app.logger.debug("Writing row %s", d)
        encoded_d = [s.encode("utf-8") if isinstance(s, unicode) else s
                     for s in d]
        writer.writerow(encoded_d)
        yield read_and_flush()
    app.logger.debug("Saving flatten data as CSV finished")
