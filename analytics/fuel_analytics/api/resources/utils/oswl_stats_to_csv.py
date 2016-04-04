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

import copy
import datetime
import itertools
import six

from fuel_analytics.api.app import app
from fuel_analytics.api.common import consts
from fuel_analytics.api.resources.utils import export_utils
from fuel_analytics.api.resources.utils.skeleton import OSWL_SKELETONS


class OswlStatsToCsv(object):

    OSWL_INDEX_FIELDS = ('master_node_uid', 'cluster_id', 'resource_type')

    def get_additional_volume_keys_paths(self):
        num = app.config['CSV_VOLUME_ATTACHMENTS_NUM']
        return export_utils.get_enumerated_keys_paths(
            consts.OSWL_RESOURCE_TYPES.volume, 'volume_attachment',
            OSWL_SKELETONS['volume_attachment'], num)

    def get_additional_keys_paths(self, resource_type):
        # Additional key paths for resource type info
        resource_additional_key_paths = [[resource_type, 'is_added'],
                                         [resource_type, 'is_modified'],
                                         [resource_type, 'is_removed']]
        if resource_type == consts.OSWL_RESOURCE_TYPES.volume:
            resource_additional_key_paths += \
                self.get_additional_volume_keys_paths()
        return resource_additional_key_paths

    def get_resource_keys_paths(self, resource_type):
        """Gets key paths for resource type. csv key paths is combination
        of oswl, vm and additional resource type key paths
        :return: tuple of lists of oswl, resource type, csv key paths
        """
        app.logger.debug("Getting %s keys paths", resource_type)
        oswl_key_paths = export_utils.get_keys_paths(OSWL_SKELETONS['general'])
        resource_key_paths = export_utils.get_keys_paths(
            {resource_type: OSWL_SKELETONS[resource_type]})

        resource_additional_key_paths = self.get_additional_keys_paths(
            resource_type)

        result_key_paths = oswl_key_paths + resource_key_paths + \
            resource_additional_key_paths

        app.logger.debug("%s keys paths got: %s", resource_type,
                         result_key_paths)
        return oswl_key_paths, resource_key_paths, result_key_paths

    def get_additional_resource_info(self, resource, resource_type,
                                     added_ids, modified_ids, removed_ids):
        """Gets additional info about operations with resource
        :param resource: resource info
        :param resource_type: resource type
        :param added_ids: set of added ids from oswl
        :param modified_ids: set of modified ids from oswl
        :param removed_ids: set of removed ids from oswl
        :return: list of integer flags: is_added, is_removed, is_modified
        """
        id_val = resource.get('id')
        is_added = id_val in added_ids
        is_modified = id_val in modified_ids
        is_removed = id_val in removed_ids
        result = [is_added, is_modified, is_removed]

        # Handling nested lists and tuples
        if resource_type == consts.OSWL_RESOURCE_TYPES.volume:
            flatten_attachments = []
            skeleton = OSWL_SKELETONS['volume_attachment']
            enum_length = (app.config['CSV_VOLUME_ATTACHMENTS_NUM'] *
                           len(skeleton))
            attachment_keys_paths = export_utils.get_keys_paths(skeleton)
            for attachment in resource.get('attachments', []):
                flatten_attachment = export_utils.get_flatten_data(
                    attachment_keys_paths, attachment)
                flatten_attachments.extend(flatten_attachment)
            result += export_utils.align_enumerated_field_values(
                flatten_attachments, enum_length)

        return result

    def handle_empty_version_info(self, oswl, clusters_versions):
        """Handles empty version info in oswl object

        For OSWLs with empty version_info data we compose version_info
        from InstallationStructure data and assign it to oswl object.
        We bound InstallationStructure.structure.clusters to the oswl
        and extract fuel_version and fuel_release from clusters data.
        If fuel_version info doesn't provided by clusters data then
        InstallationStructure.structure.fuel_release is used.

        :param oswl: OSWL DB object
        :type oswl: fuel_analytics.api.db.model.OpenStackWorkloadStats
        :param clusters_versions: cache for saving cluster versions with
        structure {mn_uid: {cluster_id: fuel_release}}
        :type clusters_versions: dict
        """
        if oswl.version_info:
            return

        # self._add_oswl_to_clusters_versions_cache(oswl, clusters_versions)

        mn_uid = oswl.master_node_uid
        cluster_id = oswl.cluster_id

        # Fetching version_info info from cache
        version_info = clusters_versions.get(mn_uid, {}).get(cluster_id)

        # If clusters data doesn't contain fuel_version we are using
        # data from installation info
        if not version_info:
            release = oswl.fuel_release_from_inst_info or {}
            version_info = {
                'fuel_version': release.get('release'),
                'release_version': release.get('openstack_version')
            }

        oswl.version_info = version_info

    def get_flatten_resources(self, resource_type, oswl_keys_paths,
                              resource_keys_paths, oswls,
                              clusters_version_info):
        """Gets flatten resources data
        :param oswl_keys_paths: list of keys paths in the OpenStack workload
        info
        :param resource_keys_paths: list of keys paths in the resource
        :param oswls: list of OpenStack workloads
        :param clusters_version_info: clusters version info cache.
        Cache is used only if version_info is not provided in the oswl.
        Cache structure: {mn_uid: {cluster_id: fuel_release}}
        :return: generator on flatten resources info collection
        """
        app.logger.debug("Getting OSWL flatten %s info started", resource_type)

        for oswl in oswls:
            try:
                self.handle_empty_version_info(oswl, clusters_version_info)
                flatten_oswl = export_utils.get_flatten_data(oswl_keys_paths,
                                                             oswl)
                resource_data = oswl.resource_data
                current = resource_data.get('current', [])
                added = resource_data.get('added', [])
                modified = resource_data.get('modified', [])
                removed = resource_data.get('removed', [])
                # Filtering wrong formatted removed data
                # delivered by old Fuel versions
                removed = [res for res in removed if len(res) > 2]

                # Extracting ids or oswl resources
                added_ids = set(item['id'] for item in added)
                modified_ids = set(item['id'] for item in modified)
                removed_ids = set(item['id'] for item in removed)

                # If resource removed and added several times it would
                # be present in current and removed. We should exclude
                # duplicates from flatten resources of the same
                # resource.
                current_ids = set(item['id'] for item in current)
                finally_removed = (res for res in removed
                                   if res['id'] not in current_ids)

                for resource in itertools.chain(current, finally_removed):
                    flatten_resource = export_utils.get_flatten_data(
                        resource_keys_paths, {resource_type: resource})
                    additional_info = self.get_additional_resource_info(
                        resource, oswl.resource_type,
                        added_ids, modified_ids, removed_ids)
                    yield flatten_oswl + flatten_resource + additional_info
            except Exception as e:
                # Generation of report should be reliable
                app.logger.error("Getting OSWL flatten data failed. "
                                 "Id: %s, master node uid: %s, "
                                 "resource_data: %s, error: %s",
                                 oswl.id, oswl.master_node_uid,
                                 oswl.resource_data, six.text_type(e))
        app.logger.debug("Getting flatten %s info finished", resource_type)

    def get_last_sync_datetime(self, oswl):
        """Gets datetime of last synchronization of masternode with
        stats collector.
        :param oswl: OpenStackWorkloadStats object with mixed info
        from InstallationStructure
        :return: datetime
        """
        return max(filter(
            lambda x: x is not None,
            (oswl.installation_created_date, oswl.installation_updated_date)))

    def stream_horizon_content(self, horizon, on_date):
        """Streams content of horizon of oswls. Obsolete
        oswls with master node last sync date < on_date will be removed
        from the horizon.
        :param horizon: dictionary of oswls, indexed by OSWL_INDEX_FIELDS
        :param on_date: date on which oswls time series is generating
        :return: generator on horizon of oswls on on_date
        """
        app.logger.debug("Streaming oswls content on date: %s", on_date)
        # Copying keys to list for make dictionary modification possible
        # during iteration through it
        keys = list(six.iterkeys(horizon))
        for key in keys:
            last_value = horizon[key]
            update_date = self.get_last_sync_datetime(last_value)
            if on_date is not None and update_date.date() < on_date:
                # Removing obsolete oswl from horizon
                horizon.pop(key)
            else:
                return_value = copy.deepcopy(last_value)
                return_value.stats_on_date = on_date
                # Removing modified, removed, added from resource data
                # if we are duplicating oswl in CSV
                if return_value.created_date != on_date:
                    return_value.resource_data['added'] = {}
                    return_value.resource_data['removed'] = {}
                    return_value.resource_data['modified'] = {}
                yield return_value

    def _add_oswl_to_horizon(self, horizon, oswl):
        idx = export_utils.get_index(oswl, *self.OSWL_INDEX_FIELDS)

        # We can have duplication of the oswls in the DB with the same
        # checksum but with different external_id. Checksum is calculated
        # by the resource_data['current'] only. Thus we shouldn't add
        # the same oswl into horizon if it already present in it and
        # has no differences in checksum and added, modified, removed
        # resources.
        old_oswl = horizon.get(idx)
        if (
            old_oswl is None or
            old_oswl.resource_checksum != oswl.resource_checksum or
            old_oswl.resource_data != oswl.resource_data
        ):
            horizon[idx] = oswl

    def fill_date_gaps(self, oswls, to_date):
        """Fills the gaps of stats info. If masternode sends stats on
        on_date and we haven't oswl on this date - the last one oswl for
        this master_node, cluster_id, resource_type will be used
        :param oswls: collection of SQLAlchemy oswl objects ordered by
        creation_date in ascending order
        :param to_date: fill gaps until this date
        :return: generator on seamless by dates oswls collection
        """
        app.logger.debug("Filling gaps in oswls started")
        horizon = {}
        last_date = None

        # Filling horizon of oswls on last date. Oswls are ordered by
        # created_date so, then last_date is changed we can assume horizon
        # of oswls is filled and can be shown
        for oswl in oswls:
            last_date = last_date or oswl.created_date
            if last_date != oswl.created_date:
                # Filling gaps in created_dates of oswls
                while last_date != oswl.created_date:
                    app.logger.debug("Filling gap on date: %s for oswl: %s",
                                     last_date, oswl.id)
                    for content in self.stream_horizon_content(
                            horizon, last_date):
                        yield content
                    last_date += datetime.timedelta(days=1)
                if last_date > to_date:
                    break

            self._add_oswl_to_horizon(horizon, oswl)

        # Filling gaps if oswls exhausted on date before to_date
        if last_date is not None:
            while last_date <= to_date:
                for content in self.stream_horizon_content(
                        horizon, last_date):
                    yield content
                last_date += datetime.timedelta(days=1)

        app.logger.debug("Filling gaps in oswls finished")

    def export(self, resource_type, oswls, to_date, clusters_version_info):
        app.logger.info("Export oswls %s info into CSV started",
                        resource_type)
        oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
            self.get_resource_keys_paths(resource_type)
        seamless_oswls = self.fill_date_gaps(
            oswls, to_date)
        flatten_resources = self.get_flatten_resources(
            resource_type, oswl_keys_paths, resource_keys_paths,
            seamless_oswls, clusters_version_info)
        result = export_utils.flatten_data_as_csv(
            csv_keys_paths, flatten_resources)
        app.logger.info("Export oswls %s info into CSV finished",
                        resource_type)
        return result
