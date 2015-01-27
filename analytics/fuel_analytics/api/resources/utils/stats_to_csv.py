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

import csv
import io
import six

from fuel_analytics.api.app import app
from fuel_analytics.api.resources.utils.skeleton import \
    INSTALLATION_INFO_SKELETON


class StatsToCsv(object):

    MANUFACTURERS_NUM = 3
    PLATFORM_NAMES_NUM = 3

    def construct_skeleton(self, data):
        """Creates structure for searching all key paths in given data
        :param data: fetched from ES dict
        :return: skeleton of data structure
        """
        if isinstance(data, dict):
            result = {}
            for k in sorted(data.keys()):
                result[k] = self.construct_skeleton(data[k])
            return result
        elif isinstance(data, (list, tuple)):
            list_result = []
            dict_result = {}
            for d in data:
                if isinstance(d, dict):
                    dict_result.update(self.construct_skeleton(d))
                elif isinstance(d, (list, tuple)):
                    if not list_result:
                        list_result.append(self.construct_skeleton(d))
                    else:
                        list_result[0].extend(self.construct_skeleton(d))
            if dict_result:
                list_result.append(dict_result)
            return list_result
        else:
            return data

    def get_data_skeleton(self, structures):
        """Gets skeleton by structures list
        :param structures:
        :return: data structure skeleton
        """
        def _merge_skeletons(lh, rh):
            keys_paths = self.get_keys_paths(rh)
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
                                         self.get_data_skeleton(data_point))
                    else:
                        merge_point[key] = None
                    merge_point = merge_point[key]

        skeleton = {}
        for structure in structures:
            app.logger.debug("Constructing skeleton by data: %s", structure)
            app.logger.debug("Updating skeleton by %s",
                             self.construct_skeleton(structure))
            _merge_skeletons(skeleton, self.construct_skeleton(structure))
            app.logger.debug("Result skeleton is %s", skeleton)
        return skeleton

    def get_keys_paths(self, skeleton):
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

    def flatten_data_as_csv(self, keys_paths, flatten_data):
        """Returns flatten data in CSV
        :param keys_paths: list of dict keys lists for columns names
        generation
        :param flatten_data: list of flatten data dicts
        :return: stream with data in CSV format
        """
        app.logger.debug("Saving flatten data as CSV is started")
        names = []
        for key_path in keys_paths:
            names.append('.'.join(key_path))
        yield names

        output = six.BytesIO()
        writer = csv.writer(output)
        writer.writerow(names)

        def read_and_flush():
            output.seek(io.SEEK_SET)
            data = output.read()
            output.seek(io.SEEK_SET)
            output.truncate()
            return data

        for d in flatten_data:
            app.logger.debug("Writing row %s", d)
            encoded_d = [s.encode("utf-8") if isinstance(s, unicode) else s
                         for s in d]
            writer.writerow(encoded_d)
            yield read_and_flush()
        app.logger.debug("Saving flatten data as CSV is finished")

    def get_flatten_data(self, keys_paths, data):
        """Creates flatten data from data by keys_paths
        :param keys_paths: list of dict keys lists
        :param data: dict with nested structures
        :return: list of flatten data dicts
        """
        flatten_data = []
        for key_path in keys_paths:
            d = data
            for key in key_path:
                d = d.get(key, None)
                if d is None:
                    break
            if isinstance(d, (list, tuple)):
                flatten_data.append(' '.join(d))
            else:
                flatten_data.append(d)
        return flatten_data

    def get_cluster_keys_paths(self):
        app.logger.debug("Getting cluster keys paths")
        structure_skeleton = INSTALLATION_INFO_SKELETON
        structure_key_paths = self.get_keys_paths(structure_skeleton)
        clusters = structure_skeleton.get('clusters')
        if not clusters:
            clusters = [{}]
        cluster_skeleton = clusters[0]

        # Removing lists of dicts from cluster skeleton
        cluster_skeleton.pop('nodes', None)
        cluster_skeleton.pop('node_groups', None)
        cluster_skeleton.pop('openstack_info', None)
        cluster_key_paths = self.get_keys_paths(cluster_skeleton)

        result_key_paths = cluster_key_paths + structure_key_paths

        def enumerated_field_keys(field_name, number):
            """Adds enumerated fields columns and property
            field for showing case, when values will be cut
            :param field_name: field name
            :param number: number of enumerated fields
            :return: list of cut fact column and enumerated columns names
            """
            result = [['{}_gt{}'.format(field_name, number)]]
            for i in xrange(number):
                result.append(['{}_{}'.format(field_name, i)])
            return result

        # Handling enumeration of manufacturers names
        result_key_paths.extend(enumerated_field_keys('nodes_manufacturer',
                                                      self.MANUFACTURERS_NUM))

        # Handling enumeration of platform names
        result_key_paths.extend(enumerated_field_keys('nodes_platform_name',
                                                      self.PLATFORM_NAMES_NUM))

        app.logger.debug("Cluster keys paths got")
        return structure_key_paths, cluster_key_paths, result_key_paths

    @staticmethod
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

    def get_flatten_clusters(self, structure_keys_paths, cluster_keys_paths,
                             structures):
        """Gets flatten clusters data
        :param structure_keys_paths: list of keys paths in the
        installation structure
        :param cluster_keys_paths: list of keys paths in the cluster
        :param structures: list of installation structures
        :return: list of flatten clusters info
        """
        app.logger.debug("Getting flatten clusters info is started")

        def extract_nodes_fields(field, nodes):
            """Extracts fields values from nested nodes dicts
            :param field: field name
            :param nodes: nodes data list
            :return: set of extracted fields values from nodes
            """
            result = set([d.get(field) for d in nodes])
            return filter(lambda x: x is not None, result)

        def extract_nodes_manufacturers(nodes):
            return extract_nodes_fields('manufacturer', nodes)

        def extract_nodes_platform_name(nodes):
            return extract_nodes_fields('platform_name', nodes)

        for structure in structures:
            clusters = structure.pop('clusters', [])
            flatten_structure = self.get_flatten_data(structure_keys_paths,
                                                      structure)
            for cluster in clusters:
                flatten_cluster = self.get_flatten_data(cluster_keys_paths,
                                                        cluster)
                flatten_cluster.extend(flatten_structure)
                nodes = cluster.get('nodes', [])

                # Adding enumerated manufacturers
                manufacturers = extract_nodes_manufacturers(nodes)
                flatten_cluster += StatsToCsv.align_enumerated_field_values(
                    manufacturers, self.MANUFACTURERS_NUM)

                # Adding enumerated platforms
                platform_names = extract_nodes_platform_name(nodes)
                flatten_cluster += StatsToCsv.align_enumerated_field_values(
                    platform_names, self.PLATFORM_NAMES_NUM)
                yield flatten_cluster

        app.logger.debug("Flatten clusters info is got")

    def export_clusters(self, structures):
        app.logger.info("Export clusters info into CSV is started")
        structure_keys_paths, cluster_keys_paths, csv_keys_paths = \
            self.get_cluster_keys_paths()
        flatten_clusters = self.get_flatten_clusters(structure_keys_paths,
                                                     cluster_keys_paths,
                                                     structures)
        result = self.flatten_data_as_csv(csv_keys_paths, flatten_clusters)
        app.logger.info("Export clusters info into CSV is finished")
        return result
