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
import copy
import six

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
        structure_skeleton = copy.deepcopy(INSTALLATION_INFO_SKELETON)
        clusters = structure_skeleton['structure'].pop('clusters')
        structure_key_paths = export_utils.get_keys_paths(structure_skeleton)
        cluster_skeleton = clusters[0]

        # Removing lists of dicts from cluster skeleton
        cluster_skeleton.pop('nodes', None)
        cluster_skeleton.pop('installed_plugins', None)
        cluster_key_paths = export_utils.get_keys_paths(cluster_skeleton)

        result_key_paths = cluster_key_paths + structure_key_paths

        # Handling network verification check
        result_key_paths.append([self.NETWORK_VERIFICATION_COLUMN])
        app.logger.debug("Cluster keys paths got")
        return structure_key_paths, cluster_key_paths, result_key_paths

    def _get_subcluster_keys_paths(self, skeleton):
        key_paths = export_utils.get_keys_paths(skeleton)
        structure_key_paths = [['master_node_uid'],
                               ['structure', 'fuel_packages']]
        cluster_key_paths = [['cluster_id'], ['cluster_fuel_version']]
        result_key_paths = key_paths + cluster_key_paths + structure_key_paths
        return structure_key_paths, cluster_key_paths, \
            key_paths, result_key_paths

    def get_plugin_keys_paths(self):
        app.logger.debug("Getting plugin keys paths")
        structure_skeleton = copy.deepcopy(INSTALLATION_INFO_SKELETON)
        clusters = structure_skeleton['structure']['clusters']
        plugin_skeleton = clusters[0]['installed_plugins'][0]
        plugin_skeleton.pop('releases', None)

        result = self._get_subcluster_keys_paths(plugin_skeleton)
        app.logger.debug("Plugin keys paths got")
        return result

    def get_node_keys_paths(self):
        app.logger.debug("Getting node keys paths")
        structure_skeleton = copy.deepcopy(INSTALLATION_INFO_SKELETON)
        clusters = structure_skeleton['structure']['clusters']
        node_skeleton = clusters[0]['nodes'][0]

        result = self._get_subcluster_keys_paths(node_skeleton)
        app.logger.debug("Node keys paths got")
        return result

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

        for inst_structure in inst_structures:
            try:
                structure = inst_structure.structure
                clusters = structure.pop('clusters', [])
                flatten_structure = export_utils.get_flatten_data(
                    structure_keys_paths, inst_structure)

                for cluster in clusters:
                    cluster.pop('installed_plugins', None)
                    flatten_cluster = export_utils.get_flatten_data(
                        cluster_keys_paths, cluster)
                    flatten_cluster.extend(flatten_structure)

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
            except Exception as e:
                # Generation of report should be reliable
                app.logger.error("Getting flatten cluster data failed. "
                                 "Installation info id: %s, "
                                 "master node uid: %s, error: %s",
                                 inst_structure.id,
                                 inst_structure.master_node_uid,
                                 six.text_type(e))
        app.logger.debug("Flatten clusters info is got")

    def get_flatten_plugins(self, structure_keys_paths, cluster_keys_paths,
                            plugin_keys_paths, inst_structures):
        """Gets flatten plugins data form clusters from installation
        structures collection
        :param structure_keys_paths: list of keys paths in the
        installation structure
        :param cluster_keys_paths: list of keys paths in the cluster
        :param plugin_keys_paths: list of keys paths in the plugin
        :param inst_structures: list of installation structures
        :return: list of flatten plugins info
        """

        return self._get_flatten_subcluster_data(
            'installed_plugins',
            structure_keys_paths,
            cluster_keys_paths,
            plugin_keys_paths,
            inst_structures
        )

    def _get_flatten_subcluster_data(self, data_path, structure_keys_paths,
                                     cluster_keys_paths, keys_paths,
                                     inst_structures):
        """Gets flatten data form clusters from installation
        structures collection
        :param structure_keys_paths: list of keys paths in the
        installation structure
        :param cluster_keys_paths: list of keys paths in the cluster
        :param keys_paths: list of keys paths in the data
        :param inst_structures: list of installation structures
        :return: list of flatten plugins info
        """
        app.logger.debug("Getting flatten %s info started", data_path)

        for inst_structure in inst_structures:
            try:
                structure = inst_structure.structure
                clusters = structure.pop('clusters', [])
                flatten_structure = export_utils.get_flatten_data(
                    structure_keys_paths, inst_structure)

                for cluster in clusters:
                    cluster['cluster_id'] = cluster['id']
                    cluster['cluster_fuel_version'] = \
                        cluster.get('fuel_version')
                    flatten_cluster = export_utils.get_flatten_data(
                        cluster_keys_paths, cluster)
                    data = cluster.pop(data_path, [])
                    for item in data:
                        flatten_data = export_utils.get_flatten_data(
                            keys_paths, item)
                        flatten_data.extend(flatten_cluster)
                        flatten_data.extend(flatten_structure)
                        yield flatten_data
            except Exception as e:
                # Generation of report should be reliable
                app.logger.error("Getting flatten %s data failed. "
                                 "Installation info id: %s, "
                                 "master node uid: %s, error: %s",
                                 data_path,
                                 inst_structure.id,
                                 inst_structure.master_node_uid,
                                 six.text_type(e))
        app.logger.debug("Getting flatten %s info finished", data_path)

    def get_flatten_nodes(self, structure_keys_paths, cluster_keys_paths,
                          node_keys_paths, inst_structures):
        """Gets flatten plugins data form clusters from installation
        structures collection
        :param structure_keys_paths: list of keys paths in the
        installation structure
        :param cluster_keys_paths: list of keys paths in the cluster
        :param node_keys_paths: list of keys paths in the node
        :param inst_structures: list of installation structures
        :return: list of flatten plugins info
        """
        return self._get_flatten_subcluster_data(
            'nodes',
            structure_keys_paths,
            cluster_keys_paths,
            node_keys_paths,
            inst_structures
        )

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

    def export_plugins(self, inst_structures):
        app.logger.info("Export plugins info into CSV started")
        (structure_keys_paths, cluster_keys_paths,
         plugin_keys_paths, csv_keys_paths) = self.get_plugin_keys_paths()
        flatten_plugins = self.get_flatten_plugins(
            structure_keys_paths, cluster_keys_paths,
            plugin_keys_paths, inst_structures)
        result = export_utils.flatten_data_as_csv(
            csv_keys_paths, flatten_plugins)
        app.logger.info("Export plugins info into CSV finished")
        return result

    def export_nodes(self, inst_structures):
        app.logger.info("Export nodes info into CSV started")
        (structure_keys_paths, cluster_keys_paths,
         node_keys_paths, csv_keys_paths) = self.get_node_keys_paths()
        flatten_nodes = self.get_flatten_nodes(
            structure_keys_paths, cluster_keys_paths,
            node_keys_paths, inst_structures)
        result = export_utils.flatten_data_as_csv(
            csv_keys_paths, flatten_nodes)
        app.logger.info("Export nodes info into CSV finished")
        return result
