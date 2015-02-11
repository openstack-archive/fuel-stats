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
# from fuel_analytics.api.resources.utils.skeleton import \
#     OSWL_STATS_SKELETON
# from fuel_analytics.api.resources.utils.skeleton import \
#     OSWL_VM_SKELETON


class OswlStatsToCsv(object):

    def get_vm_keys_paths(self, resource_type='vm'):
        """Gets key paths for resource type. csv key paths is combination
        of oswl, vm and additional resource type key paths
        :return: tuple of lists of oswl, resource type, csv key paths
        """
        app.logger.debug("Getting %s keys paths", resource_type)
        oswl_key_paths = get_keys_paths(OSWL_SKELETONS['general'])
        vm_key_paths = get_keys_paths({resource_type: OSWL_SKELETONS[resource_type]})

        # Additional key paths for resource type info
        vm_additional_key_paths = [[resource_type, 'is_added'],
                                   [resource_type, 'is_modified'],
                                   [resource_type, 'is_removed']]
        result_key_paths = oswl_key_paths + vm_key_paths + \
            vm_additional_key_paths

        app.logger.debug("%s keys paths got", resource_type)
        return oswl_key_paths, vm_key_paths, result_key_paths

    def get_additional_vm_info(self, vm, oswl):
        """Gets additional info about vm operations
        :param vm: vm info
        :param oswl: OpenStack workload
        :return: list of is_added, is_removed, is_modified flags
        """
        resource_data = oswl.resource_data
        added = resource_data.get('added', {})
        removed = resource_data.get('removed', {})
        modified = resource_data.get('modified', {})
        # After JSON saving in the object dict keys are converted into strings
        vm_id = six.text_type(vm.get('id'))
        is_added = vm_id in added
        is_modified = vm_id in modified
        is_removed = vm_id in removed
        return [is_added, is_modified, is_removed]

    def get_flatten_vms(self, oswl_keys_paths, vm_keys_paths, oswls):
        """Gets flatten vms data
        :param oswl_keys_paths: list of keys paths in the OpenStack workload
        info
        :param vm_keys_paths: list of keys paths in the vm
        :param oswls: list of OpenStack workloads
        :return: list of flatten vms info
        """
        app.logger.debug("Getting flatten vms info is started")
        for oswl in oswls:
            flatten_oswl = export_utils.get_flatten_data(oswl_keys_paths,
                                                         oswl)
            resource_data = oswl.resource_data
            current = resource_data.get('current', [])
            removed = resource_data.get('removed', {})
            for vm in itertools.chain(current, six.itervalues(removed)):
                flatten_vm = export_utils.get_flatten_data(vm_keys_paths,
                                                           {'vm': vm})
                vm_additional_info = self.get_additional_vm_info(vm, oswl)
                yield flatten_oswl + flatten_vm + vm_additional_info
        app.logger.debug("Flatten vms info is got")

    def export_vms(self, oswls):
        app.logger.info("Export oswls vms info into CSV is started")
        oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
            self.get_vm_keys_paths()
        flatten_vms = self.get_flatten_vms(oswl_keys_paths, vm_keys_paths,
                                           oswls)
        result = export_utils.flatten_data_as_csv(csv_keys_paths, flatten_vms)
        app.logger.info("Export oswls vms info into CSV is finished")
        return result

    def export(self, resource_type):
        app.logger.info("Export oswls %s info into CSV is started",
                        resource_type)
        oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
            self.get_vm_keys_paths(resource_type=resource_type)
        # flatten_vms = self.get_flatten_vms(oswl_keys_paths, vm_keys_paths,
        #                                    oswls)
        # result = export_utils.flatten_data_as_csv(csv_keys_paths, flatten_vms)
        # app.logger.info("Export oswls vms info into CSV is finished")
        # return result
