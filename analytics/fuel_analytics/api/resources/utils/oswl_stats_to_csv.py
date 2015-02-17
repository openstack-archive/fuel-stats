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

import itertools
import six

from fuel_analytics.api.app import app
from fuel_analytics.api.resources.utils import export_utils
from fuel_analytics.api.resources.utils.export_utils import get_keys_paths
from fuel_analytics.api.resources.utils.skeleton import OSWL_SKELETONS


class OswlStatsToCsv(object):

    def get_resource_keys_paths(self, resource_type):
        """Gets key paths for resource type. csv key paths is combination
        of oswl, vm and additional resource type key paths
        :return: tuple of lists of oswl, resource type, csv key paths
        """
        app.logger.debug("Getting %s keys paths", resource_type)
        oswl_key_paths = get_keys_paths(OSWL_SKELETONS['general'])
        vm_key_paths = get_keys_paths(
            {resource_type: OSWL_SKELETONS[resource_type]})

        # Additional key paths for resource type info
        vm_additional_key_paths = [[resource_type, 'is_added'],
                                   [resource_type, 'is_modified'],
                                   [resource_type, 'is_removed']]
        result_key_paths = oswl_key_paths + vm_key_paths + \
            vm_additional_key_paths

        app.logger.debug("%s keys paths got: %s", resource_type,
                         result_key_paths)
        return oswl_key_paths, vm_key_paths, result_key_paths

    def get_additional_resource_info(self, resource, oswl):
        """Gets additional info about operations with resource
        :param resource: resource info
        :param oswl: OpenStack workload
        :return: list of integer flags: is_added, is_removed, is_modified
        """
        resource_data = oswl.resource_data
        added = resource_data.get('added', {})
        removed = resource_data.get('removed', {})
        modified = resource_data.get('modified', {})
        # After JSON saving in the object dict keys are converted into strings
        vm_id = six.text_type(resource.get('id'))
        is_added = vm_id in added
        is_modified = vm_id in modified
        is_removed = vm_id in removed
        return [is_added, is_modified, is_removed]

    def get_flatten_resources(self, resource_type, oswl_keys_paths,
                              resource_keys_paths, oswls):
        """Gets flatten vms data
        :param oswl_keys_paths: list of keys paths in the OpenStack workload
        info
        :param resource_keys_paths: list of keys paths in the resource
        :param oswls: list of OpenStack workloads
        :return: list of flatten resources info
        """
        app.logger.debug("Getting flatten %s info started", resource_type)
        for oswl in oswls:
            flatten_oswl = export_utils.get_flatten_data(oswl_keys_paths,
                                                         oswl)
            resource_data = oswl.resource_data
            current = resource_data.get('current', [])
            removed = resource_data.get('removed', {})
            for resource in itertools.chain(current, six.itervalues(removed)):
                flatten_resource = export_utils.get_flatten_data(
                    resource_keys_paths, {resource_type: resource})
                additional_info = self.get_additional_resource_info(
                    resource, oswl)
                yield flatten_oswl + flatten_resource + additional_info
        app.logger.debug("Getting flatten %s info finished", resource_type)

    def get_last_sync_date(self, oswl):
        return max(filter(
            lambda x: x is not None,
            (oswl.installation_created_date, oswl.installation_updated_date)))

    def fill_date_gaps(self, oswls):
        """
        :param oswls: ordered by creation_date oswls
        :return:
        """
        app.logger.debug("Filling gaps in oswls started")
        horizon = {}
        last_date = None

        def stream_horizon_content(on_date):
            for mn_uid, last_value in six.iteritems(horizon):
                update_date = self.get_last_sync_date(last_value)
                if on_date is not None and update_date < on_date:
                    horizon.pop(mn_uid)
                else:
                    yield last_value

        for oswl in oswls:
            if last_date != oswl.created_date:
                stream_horizon_content(last_date)
                last_date = oswl.created_date
            horizon[oswl.master_node_uid] = oswl
        stream_horizon_content(last_date)
        app.logger.debug("Filling gaps in oswls finished")

    def export(self, resource_type, oswls):
        app.logger.info("Export oswls %s info into CSV started",
                        resource_type)
        oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
            self.get_resource_keys_paths(resource_type)
        seamless_oswls = self.fill_date_gaps(oswls)

        # In case of oswls has no items
        if seamless_oswls is None:
            seamless_oswls = ()

        flatten_resources = self.get_flatten_resources(
            resource_type, oswl_keys_paths, vm_keys_paths, seamless_oswls)
        result = export_utils.flatten_data_as_csv(csv_keys_paths,
                                                  flatten_resources)
        app.logger.info("Export oswls %s info into CSV finished",
                        resource_type)
        return result
