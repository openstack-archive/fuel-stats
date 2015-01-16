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

import csv
import io
import six


class StatsToCsv(object):

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
        skeleton = {}
        for structure in structures:
            skeleton.update(self.construct_skeleton(structure))
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
        names = []
        for key_path in keys_paths:
            names.append('.'.join(key_path))
        output = io.BytesIO()
        writer = csv.writer(output)
        writer.writerow(names)
        for d in flatten_data:
            writer.writerow(d)
        return output

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

    def get_flatten_clusters(self, structures):
        """Gets flatten clusters data
        :param structures: list of installation structures
        :return: list of flatten clusters info
        """
        structure_skeleton = self.get_data_skeleton(structures)
        structure_key_paths = self.get_keys_paths(structure_skeleton)
        clusters = structure_skeleton.get('clusters')
        if not clusters:
            clusters = [{}]
        cluster_skeleton = clusters[0]
        # Removing lists of dicts from cluster skeleton
        cluster_skeleton.pop('nodes', None)
        cluster_skeleton.pop('node_groups', None)
        cluster_key_paths = self.get_keys_paths(cluster_skeleton)

        def extract_nodes_fields(field, nodes):
            result = set([d.get(field) for d in nodes])
            return filter(lambda x: x is not None, result)

        def extract_nodes_manufacturers(nodes):
            return extract_nodes_fields('manufacturer', nodes)

        def extract_nodes_platform_name(nodes):
            return extract_nodes_fields('platform_name', nodes)

        def enumerated_field_keys(field_name, number):
            result = [['{}_gt{}'.format(field_name, number)]]
            for i in xrange(number):
                result.append(['{}_{}'.format(field_name, i)])
            return result

        def align_enumerated_field_values(values, number):
            return ([len(values) >= number] +
                    (values + [None] * (number - len(values)))[:number])

        result_flatten_data = []
        result_key_paths = cluster_key_paths + structure_key_paths

        # Handling enumeration of manufacturers names
        manufacturers_num = 3
        result_key_paths.extend(enumerated_field_keys('nodes_manufacturer',
                                                      manufacturers_num))

        # Handling enumeration of platform names
        platform_names_num = 3
        result_key_paths.extend(enumerated_field_keys('nodes_platform_name',
                                                      platform_names_num))

        for structure in structures:
            clusters = structure.pop('clusters', [])
            flatten_structure = self.get_flatten_data(structure_key_paths,
                                                      structure)
            for cluster in clusters:
                flatten_cluster = self.get_flatten_data(cluster_key_paths,
                                                        cluster)
                flatten_cluster.extend(flatten_structure)
                nodes = cluster.get('nodes', [])

                # Adding enumerated manufacturers
                manufacturers = extract_nodes_manufacturers(nodes)
                flatten_cluster += align_enumerated_field_values(
                    manufacturers, manufacturers_num)

                # Adding enumerated platforms
                platform_names = extract_nodes_platform_name(nodes)
                flatten_cluster += align_enumerated_field_values(
                    platform_names, platform_names_num)

                result_flatten_data.append(flatten_cluster)
        return result_key_paths, result_flatten_data

    def export_clusters(self, structures):
        cluster_key_paths, flatten_clusters = self.get_flatten_clusters(
            structures)
        output = self.flatten_data_as_csv(cluster_key_paths, flatten_clusters)
        return output.getvalue()
