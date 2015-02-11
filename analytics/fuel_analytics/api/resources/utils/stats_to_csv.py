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

from six.moves import range

from fuel_analytics.api.app import app
from fuel_analytics.api.resources.utils import export_utils
from fuel_analytics.api.resources.utils.skeleton import \
    INSTALLATION_INFO_SKELETON


class StatsToCsv(object):

    MANUFACTURERS_NUM = 3
    PLATFORM_NAMES_NUM = 3

    def get_cluster_keys_paths(self):
        app.logger.debug("Getting cluster keys paths")
        structure_skeleton = INSTALLATION_INFO_SKELETON
        structure_key_paths = export_utils.get_keys_paths(structure_skeleton)
        clusters = structure_skeleton.get('clusters')
        if not clusters:
            clusters = [{}]
        cluster_skeleton = clusters[0]

        # Removing lists of dicts from cluster skeleton
        cluster_skeleton.pop('nodes', None)
        cluster_skeleton.pop('node_groups', None)
        cluster_skeleton.pop('openstack_info', None)
        cluster_key_paths = export_utils.get_keys_paths(cluster_skeleton)

        result_key_paths = cluster_key_paths + structure_key_paths

        def enumerated_field_keys(field_name, number):
            """Adds enumerated fields columns and property
            field for showing case, when values will be cut
            :param field_name: field name
            :param number: number of enumerated fields
            :return: list of cut fact column and enumerated columns names
            """
            result = [['{}_gt{}'.format(field_name, number)]]
            for i in range(number):
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
            flatten_structure = export_utils.get_flatten_data(
                structure_keys_paths, structure)
            for cluster in clusters:
                flatten_cluster = export_utils.get_flatten_data(
                    cluster_keys_paths, cluster)
                flatten_cluster.extend(flatten_structure)
                nodes = cluster.get('nodes', [])

                # Adding enumerated manufacturers
                manufacturers = extract_nodes_manufacturers(nodes)
                flatten_cluster += export_utils.align_enumerated_field_values(
                    manufacturers, self.MANUFACTURERS_NUM)

                # Adding enumerated platforms
                platform_names = extract_nodes_platform_name(nodes)
                flatten_cluster += export_utils.align_enumerated_field_values(
                    platform_names, self.PLATFORM_NAMES_NUM)
                yield flatten_cluster

        app.logger.debug("Flatten clusters info is got")

    def export_clusters(self, structures):
        app.logger.info("Export clusters info into CSV started")
        structure_keys_paths, cluster_keys_paths, csv_keys_paths = \
            self.get_cluster_keys_paths()
        flatten_clusters = self.get_flatten_clusters(structure_keys_paths,
                                                     cluster_keys_paths,
                                                     structures)
        result = export_utils.flatten_data_as_csv(csv_keys_paths,
                                                  flatten_clusters)
        app.logger.info("Export clusters info into CSV finished")
        return result
