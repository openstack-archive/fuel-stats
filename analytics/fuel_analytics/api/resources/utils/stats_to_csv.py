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

import collections
from six.moves import range

from fuel_analytics.api.app import app
from fuel_analytics.api.resources.utils import export_utils
from fuel_analytics.api.resources.utils.skeleton import \
    INSTALLATION_INFO_SKELETON


ActionLogInfo = collections.namedtuple(
    'ActionLogInfo', ['external_id', 'master_node_uid', 'cluster_id',
                      'status', 'end_datetime', 'action_name'])


class StatsToCsv(object):

    MANUFACTURERS_NUM = 3
    PLATFORM_NAMES_NUM = 3

    ACTION_LOG_INDEX_FIELDS = ('master_node_uid', 'cluster_id', 'action_name')
    NETWORK_VERIFICATION_COLUMN = 'verify_networks_status'
    NETWORK_VERIFICATION_ACTION = 'verify_networks'

    def get_cluster_keys_paths(self):
        app.logger.debug("Getting cluster keys paths")
        structure_skeleton = INSTALLATION_INFO_SKELETON
        structure_key_paths = export_utils.get_keys_paths(structure_skeleton)
        clusters = structure_skeleton['structure']['clusters']
        cluster_skeleton = clusters[0]

        # Removing lists of dicts from cluster skeleton
        cluster_skeleton.pop('nodes', None)
        cluster_skeleton.pop('node_groups', None)
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

        # Handling network verification check
        result_key_paths.append([self.NETWORK_VERIFICATION_COLUMN])
        app.logger.debug("Cluster keys paths got")
        return structure_key_paths, cluster_key_paths, result_key_paths

    def build_action_logs_idx(self, action_logs):
        app.logger.debug("Building action logs index started")
        action_logs_idx = {}
        for action_log in action_logs:
            idx = export_utils.get_index(
                action_log, *self.ACTION_LOG_INDEX_FIELDS)
            action_logs_idx[idx] = ActionLogInfo(*action_log)
        app.logger.debug("Building action logs index finished")
        return action_logs_idx

    def get_flatten_clusters(self, structure_keys_paths, cluster_keys_paths,
                             inst_structures, action_logs):
        """Gets flatten clusters data form installation structures collection
        :param structure_keys_paths: list of keys paths in the
        installation structure
        :param cluster_keys_paths: list of keys paths in the cluster
        :param inst_structures: list of installation structures
        :param action_logs: list of action logs
        :return: list of flatten clusters info
        """
        app.logger.debug("Getting flatten clusters info is started")
        action_logs_idx = self.build_action_logs_idx(action_logs)

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

        for inst_structure in inst_structures:
            structure = inst_structure.structure
            clusters = structure.pop('clusters', [])
            print "### clusters", clusters
            flatten_structure = export_utils.get_flatten_data(
                structure_keys_paths, inst_structure)

            for cluster in clusters:
                flatten_cluster = export_utils.get_flatten_data(
                    cluster_keys_paths, cluster)
                flatten_cluster.extend(flatten_structure)
                nodes = cluster.get('nodes', [])
                print "### nodes", nodes

                # Adding enumerated manufacturers
                manufacturers = extract_nodes_manufacturers(nodes)
                print "### manufacturers", manufacturers
                flatten_cluster += export_utils.align_enumerated_field_values(
                    manufacturers, self.MANUFACTURERS_NUM)

                # Adding enumerated platforms
                platform_names = extract_nodes_platform_name(nodes)
                print "### platform_names", platform_names
                flatten_cluster += export_utils.align_enumerated_field_values(
                    platform_names, self.PLATFORM_NAMES_NUM)

                # Adding network verification status
                idx = export_utils.get_index(
                    {'master_node_uid': inst_structure.master_node_uid,
                     'cluster_id': cluster['id'],
                     'action_name': self.NETWORK_VERIFICATION_ACTION},
                    *self.ACTION_LOG_INDEX_FIELDS
                )
                al_info = action_logs_idx.get(idx)
                nv_status = None if al_info is None else al_info.status
                flatten_cluster.append(nv_status)
                yield flatten_cluster

        app.logger.debug("Flatten clusters info is got")

    def export_clusters(self, inst_structures, action_logs):
        app.logger.info("Export clusters info into CSV started")
        structure_keys_paths, cluster_keys_paths, csv_keys_paths = \
            self.get_cluster_keys_paths()
        flatten_clusters = self.get_flatten_clusters(
            structure_keys_paths, cluster_keys_paths,
            inst_structures, action_logs)
        result = export_utils.flatten_data_as_csv(
            csv_keys_paths, flatten_clusters)
        app.logger.info("Export clusters info into CSV finished")
        return result
