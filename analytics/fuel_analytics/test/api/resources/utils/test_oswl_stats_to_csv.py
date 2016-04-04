# -*- coding: utf-8 -*-

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
from datetime import datetime
from datetime import timedelta
import mock
import six
import types
import uuid

from fuel_analytics.test.api.resources.utils.oswl_test import OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
from fuel_analytics.api.db.model import InstallationStructure
from fuel_analytics.api.db.model import OpenStackWorkloadStats
from fuel_analytics.api.resources.csv_exporter import get_clusters_version_info
from fuel_analytics.api.resources.csv_exporter import get_oswls
from fuel_analytics.api.resources.csv_exporter import get_oswls_query
from fuel_analytics.api.resources.utils import export_utils
from fuel_analytics.api.resources.utils.oswl_stats_to_csv import OswlStatsToCsv
from fuel_analytics.api.resources.utils.skeleton import OSWL_SKELETONS


class OswlStatsToCsvTest(OswlTest, DbTest):

    def test_get_keys_paths(self):
        for resource_type in self.RESOURCE_TYPES:
            exporter = OswlStatsToCsv()
            oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
                exporter.get_resource_keys_paths(resource_type)
            self.assertNotIn(['external_id'], oswl_keys_paths)
            self.assertNotIn(['updated_time'], oswl_keys_paths)
            self.assertNotIn(['release'], oswl_keys_paths)
            self.assertIn(['version_info', 'fuel_version'], oswl_keys_paths)
            self.assertIn(['version_info', 'release_version'],
                          oswl_keys_paths)
            self.assertIn(['version_info', 'release_name'], oswl_keys_paths)
            self.assertIn(['version_info', 'release_os'], oswl_keys_paths)
            self.assertIn(['version_info', 'environment_version'],
                          oswl_keys_paths)
            self.assertIn([resource_type, 'id'], resource_keys_paths)
            self.assertIn([resource_type, 'is_added'], csv_keys_paths)
            self.assertIn([resource_type, 'is_modified'], csv_keys_paths)
            self.assertIn([resource_type, 'is_removed'], csv_keys_paths)

    def test_get_flatten_resources(self):
        for resource_type in self.RESOURCE_TYPES:
            exporter = OswlStatsToCsv()
            oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
                exporter.get_resource_keys_paths(resource_type)
            oswls = self.generate_oswls(2, resource_type)
            flatten_resources = exporter.get_flatten_resources(
                resource_type, oswl_keys_paths, resource_keys_paths, oswls, {})
            self.assertTrue(isinstance(flatten_resources, types.GeneratorType))
            for _ in flatten_resources:
                pass

    def test_flavor_ephemeral_in_flatten(self):
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.flavor
        oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
            exporter.get_resource_keys_paths(resource_type)
        oswls = self.generate_oswls(1, resource_type)
        flatten_resources = exporter.get_flatten_resources(
            resource_type, oswl_keys_paths, resource_keys_paths, oswls, {})

        ephemeral_idx = csv_keys_paths.index(['flavor', 'ephemeral'])
        for fr in flatten_resources:
            self.assertIsNotNone(fr[ephemeral_idx])

    def test_get_additional_info(self):
        exporter = OswlStatsToCsv()
        added_num = 0
        modified_num = 3
        removed_num = 5
        num = 1
        for resource_type in self.RESOURCE_TYPES:
            oswls = self.generate_oswls(
                num,
                resource_type,
                added_num_range=(added_num, added_num),
                modified_num_range=(modified_num, modified_num),
                removed_num_range=(removed_num, removed_num)
            )
            oswl = oswls.next()

            # Saving data for true JSON loading from DB object
            db.session.add(oswl)
            resource_data = oswl.resource_data
            added_ids = set(d['id'] for d in resource_data['added'])
            modified_ids = set(d['id'] for d in resource_data['modified'])
            removed_ids = set(d['id'] for d in resource_data['removed'])
            for resource in resource_data['current']:
                resource_id = resource['id']
                expected = [
                    resource_id in added_ids,
                    resource_id in modified_ids,
                    resource_id in removed_ids
                ]
                # In case of CSV_VOLUME_ATTACHMENTS_NUM > 0
                # additional info of volume will be extended by attachments
                # info. Attachments handling is tested in the method
                # test_volumes_attachments
                with mock.patch.dict(app.config,
                                     {'CSV_VOLUME_ATTACHMENTS_NUM': 0}):
                    added_ids = set(item['id'] for item in
                                    resource_data.get('added', []))
                    modified_ids = set(item['id'] for item in
                                       resource_data.get('removed', []))
                    removed_ids = set(item['id'] for item in
                                      resource_data.get('modified', []))

                    actual = exporter.get_additional_resource_info(
                        resource, oswl.resource_type,
                        added_ids, modified_ids, removed_ids)
                self.assertListEqual(expected, actual)

    def test_export(self):
        exporter = OswlStatsToCsv()
        num = 200
        with app.test_request_context():
            for resource_type in self.RESOURCE_TYPES:
                # Saving data for true JSON loading from DB object
                oswls_saved = self.get_saved_oswls(num, resource_type)
                # Saving installation structures for proper oswls filtering
                self.get_saved_inst_structs(oswls_saved)
                # Checking oswls filtered properly
                oswls = list(get_oswls(resource_type))
                self.assertEqual(num, len(oswls))
                # Checking export
                result = exporter.export(resource_type, oswls, {},
                                         datetime.utcnow().date())
                self.assertTrue(isinstance(result, types.GeneratorType))
                output = six.StringIO(list(result))
                reader = csv.reader(output)
                for _ in reader:
                    pass

    def test_export_on_empty_data(self):
        exporter = OswlStatsToCsv()
        for resource_type in self.RESOURCE_TYPES:
            result = exporter.export(resource_type, [], {}, None)
            self.assertTrue(isinstance(result, types.GeneratorType))
            output = six.StringIO(list(result))
            reader = csv.reader(output)
            for _ in reader:
                pass

    def test_get_last_sync_datetime(self):
        exporter = OswlStatsToCsv()
        for resource_type in self.RESOURCE_TYPES:
            oswls_saved = self.get_saved_oswls(1, resource_type)
            inst_sturcts = self.get_saved_inst_structs(oswls_saved)
            inst_struct = inst_sturcts[0]
            inst_struct.modification_date = None

            oswls = get_oswls_query(resource_type).all()
            oswl = oswls[0]
            self.assertEquals(
                inst_struct.creation_date,
                exporter.get_last_sync_datetime(oswl)
            )

            inst_struct.modification_date = datetime.utcnow()
            oswls = get_oswls_query(resource_type).all()
            oswl = oswls[0]
            self.assertEquals(
                inst_struct.modification_date,
                exporter.get_last_sync_datetime(oswl)
            )

    def test_stream_horizon_content(self):
        exporter = OswlStatsToCsv()
        created_days = 2
        for resource_type in self.RESOURCE_TYPES:
            # Generating oswl on specified date
            oswls_saved = self.get_saved_oswls(
                1, resource_type, created_date_range=(created_days,
                                                      created_days))
            self.get_saved_inst_structs(
                oswls_saved, creation_date_range=(created_days, created_days))

            oswls = get_oswls_query(resource_type).all()
            oswl = oswls[0]
            oswl_idx = export_utils.get_index(
                oswl, *exporter.OSWL_INDEX_FIELDS)
            horizon = {
                oswl_idx: oswl
            }

            # Checking horizon size is changed on date greater than specified
            # date. Checks list format: [(on_date, horizon_size)]
            checks = [
                (datetime.utcnow().date() - timedelta(days=created_days + 1),
                 1),
                (datetime.utcnow().date() - timedelta(days=created_days),
                 1),
                (datetime.utcnow().date() - timedelta(days=created_days - 1),
                 0),
            ]
            for on_date, horizon_size in checks:
                for _ in exporter.stream_horizon_content(horizon, on_date):
                    pass
                self.assertEqual(horizon_size, len(horizon))

    def test_fill_date_gaps(self):
        exporter = OswlStatsToCsv()
        created_days = 5
        for resource_type in self.RESOURCE_TYPES:
            # Generating resource time series for one master node
            oswls_saved = self.get_saved_oswls(
                1, resource_type, created_date_range=(created_days,
                                                      created_days))
            inst_sturcts = self.get_saved_inst_structs(
                oswls_saved, creation_date_range=(created_days, created_days))
            inst_struct = inst_sturcts[0]

            # Checking only one record is present
            inst_struct.modification_date = None
            db.session.add(inst_struct)
            oswls = get_oswls_query(resource_type).all()
            oswl = oswls[0]
            self.assertIsNotNone(oswl.installation_created_date)
            self.assertIsNone(oswl.installation_updated_date)

            oswls_seamless = exporter.fill_date_gaps(
                oswls, datetime.utcnow().date())
            self.assertEquals(1, len(list(oswls_seamless)))

            # Checking record is duplicated
            inst_struct.modification_date = datetime.utcnow()
            db.session.add(inst_struct)

            oswls = get_oswls_query(resource_type).all()
            oswl = oswls[0]
            self.assertIsNotNone(oswl.installation_created_date)
            self.assertIsNotNone(oswl.installation_updated_date)

            on_date_days = 1
            on_date = (datetime.utcnow() - timedelta(days=on_date_days)).date()
            oswls_seamless = list(exporter.fill_date_gaps(oswls, on_date))
            self.assertEquals(created_days - on_date_days + 1,
                              len(oswls_seamless))

            # Checking dates are seamless and grow
            expected_date = oswls_seamless[0].stats_on_date
            for oswl in oswls_seamless:
                self.assertEqual(expected_date, oswl.stats_on_date)
                expected_date += timedelta(days=1)

    def test_fill_date_gaps_empty_data_is_not_failed(self):
        exporter = OswlStatsToCsv()
        oswls = exporter.fill_date_gaps([], datetime.utcnow().date())
        self.assertTrue(isinstance(oswls, types.GeneratorType))

    def test_resource_data_on_oswl_duplication(self):
        exporter = OswlStatsToCsv()
        num = 20
        for resource_type in self.RESOURCE_TYPES:
            oswls_before = get_oswls_query(resource_type).count()
            oswls_saved = self.get_saved_oswls(
                num, resource_type,
                added_num_range=(1, 5), removed_num_range=(1, 3),
                modified_num_range=(1, 15)
            )
            self.get_saved_inst_structs(oswls_saved,
                                        creation_date_range=(0, 0))
            oswls = get_oswls_query(resource_type).all()
            self.assertEquals(oswls_before + num, len(list(oswls)))

            # Checking added, modified, removed not empty
            for oswl in oswls:
                resource_data = oswl.resource_data
                self.assertTrue(len(resource_data['added']) > 0)
                self.assertTrue(len(resource_data['modified']) > 0)
                self.assertTrue(len(resource_data['removed']) > 0)

            # Checking added, modified, removed empty on duplicated oswls
            oswls_seamless = exporter.fill_date_gaps(
                oswls, datetime.utcnow().date())
            for oswl in oswls_seamless:
                if oswl.created_date != oswl.stats_on_date:
                    resource_data = oswl.resource_data
                    self.assertEqual(0, len(resource_data['added']))
                    self.assertEqual(0, len(resource_data['modified']))
                    self.assertEqual(0, len(resource_data['removed']))

    def test_fill_date_gaps_for_set_of_clusters(self):
        exporter = OswlStatsToCsv()
        created_days = 3
        clusters_num = 2
        insts_num = 3
        for resource_type in self.RESOURCE_TYPES[:1]:
            # Generating oswls
            for _ in six.moves.range(insts_num):
                mn_uid = six.text_type(uuid.uuid4())
                oswls_saved = []
                for cluster_id in six.moves.range(clusters_num):
                    created_date = datetime.utcnow().date() - \
                        timedelta(days=created_days)
                    oswl = OpenStackWorkloadStats(
                        master_node_uid=mn_uid,
                        external_id=cluster_id,
                        cluster_id=cluster_id,
                        created_date=created_date,
                        updated_time=datetime.utcnow().time(),
                        resource_type=resource_type,
                        resource_checksum='',
                        resource_data={}
                    )
                    db.session.add(oswl)
                    oswls_saved.append(oswl)
                self.get_saved_inst_structs(oswls_saved,
                                            creation_date_range=(0, 0))
            # Checking all resources in seamless oswls
            oswls = get_oswls_query(resource_type).all()
            self.assertEquals(insts_num * clusters_num, len(oswls))
            oswls_seamless = list(exporter.fill_date_gaps(
                oswls, datetime.utcnow().date()))
            self.assertEqual(insts_num * clusters_num * (created_days + 1),
                             len(list(oswls_seamless)))

            # Checking dates do not decrease in seamless oswls
            dates = [oswl.stats_on_date for oswl in oswls_seamless]
            self.assertListEqual(sorted(dates), dates)

    def test_filter_by_date(self):
        exporter = OswlStatsToCsv()
        num = 10
        with app.test_request_context('/?from_date=2015-02-01'):
            for resource_type in self.RESOURCE_TYPES:
                # Creating oswls
                oswls_saved = self.get_saved_oswls(num, resource_type)
                self.get_saved_inst_structs(oswls_saved)
                # Filtering oswls
                oswls = get_oswls(resource_type)
                result = exporter.export(resource_type, oswls, {},
                                         datetime.utcnow().date())
                self.assertTrue(isinstance(result, types.GeneratorType))
                output = six.StringIO(list(result))
                reader = csv.reader(output)
                for _ in reader:
                    pass

    def test_seamless_dates(self):
        exporter = OswlStatsToCsv()
        # Creating oswls with not continuous created dates
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        old_days = 7
        new_days = 2
        oswls_saved = [
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=1,
                cluster_id=1,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=old_days)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='',
                resource_data={}
            ),
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=2,
                cluster_id=2,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=new_days)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='',
                resource_data={}
            ),
        ]
        for oswl in oswls_saved:
            db.session.add(oswl)
        self.get_saved_inst_structs(oswls_saved, creation_date_range=(0, 0))

        with app.test_request_context():
            oswls = get_oswls(resource_type)
        oswls_seamless = list(exporter.fill_date_gaps(
            oswls, datetime.utcnow().date()))

        # Checking size of seamless report
        single_record = old_days - new_days
        number_of_records = new_days + 1  # current date should be in report
        expected_num = single_record + number_of_records * len(oswls_saved)
        actual_num = len(oswls_seamless)
        self.assertEqual(expected_num, actual_num)

        # Checking no gaps in dates
        stats_on_date = oswls_seamless[0].stats_on_date
        for o in oswls_seamless:
            self.assertIn(
                o.stats_on_date - stats_on_date,
                (timedelta(days=0), timedelta(days=1))
            )
            stats_on_date = o.stats_on_date

    def test_dates_filtering(self):
        updated_at = datetime.utcnow()
        base_date = updated_at.date() - timedelta(days=1)
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        oswl = OpenStackWorkloadStats(
            master_node_uid='x',
            external_id=1,
            cluster_id=1,
            created_date=base_date,
            updated_time=updated_at.time(),
            resource_type=resource_type,
            resource_checksum='',
            resource_data={'current': [{'id': 444, 'status': 'ACTIVE'}]}
        )
        db.session.add(oswl)
        self.get_saved_inst_structs([oswl], creation_date_range=(0, 0))

        req_params = '/?from_date={0}&to_date={1}'.format(
            (base_date - timedelta(days=2)).isoformat(),
            (base_date - timedelta(days=1)).isoformat()
        )
        with app.test_request_context(req_params):
            oswls = list(get_oswls(resource_type))
            self.assertEqual(0, len(oswls))
            result = exporter.export(
                resource_type,
                oswls,
                (base_date - timedelta(days=1)),
                {}
            )
            # Only column names in result
            self.assertEqual(1, len(list(result)))

        req_params = '/?to_date={0}'.format(
            (base_date - timedelta(days=1)).isoformat()
        )
        with app.test_request_context(req_params):
            oswls = list(get_oswls(resource_type))
            self.assertEqual(0, len(oswls))
            result = exporter.export(
                resource_type,
                oswls,
                base_date - timedelta(days=1),
                {}
            )
            # Only column names in result
            self.assertEqual(1, len(list(result)))

        req_params = '/?_date={0}'.format(
            base_date.isoformat()
        )
        with app.test_request_context(req_params):
            oswls = list(get_oswls(resource_type))
            self.assertEqual(1, len(oswls))
            result = exporter.export(
                resource_type,
                oswls,
                {},
                base_date + timedelta(days=1)
            )
            # Not only column names in result
            self.assertEqual(1 + 2, len(list(result)))

    def test_resource_data_structure(self):
        num = 20
        for resource_type in self.RESOURCE_TYPES:
            oswls = self.get_saved_oswls(num, resource_type)
            for oswl in oswls:
                for res_data in oswl.resource_data['current']:
                    # Checking all required for report data is in resource data
                    for key in six.iterkeys(OSWL_SKELETONS[resource_type]):
                        self.assertIn(key, res_data)

    def test_volumes_attachments(self):
        exporter = OswlStatsToCsv()
        num = 100
        resource_type = consts.OSWL_RESOURCE_TYPES.volume
        with app.test_request_context():
            oswls_saved = self.get_saved_oswls(
                num, resource_type, current_num_range=(1, 1),
                removed_num_range=(0, 0))

            # Saving installation structures for proper oswls filtering
            self.get_saved_inst_structs(oswls_saved)

            oswls = list(get_oswls(resource_type))
            oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
                exporter.get_resource_keys_paths(resource_type)
            flatten_volumes = exporter.get_flatten_resources(
                resource_type, oswl_keys_paths, vm_keys_paths, oswls, {})
            flatten_volumes = list(flatten_volumes)

            csv_att_num = app.config['CSV_VOLUME_ATTACHMENTS_NUM']
            gt_field_pos = csv_keys_paths.index([
                resource_type, 'volume_attachment_gt_{}'.format(csv_att_num)])
            for idx, fv in enumerate(flatten_volumes):
                oswl = oswls[idx]
                # Checking CSV fields alignment
                self.assertEqual(len(csv_keys_paths), len(fv))
                # Checking gt field calculation
                volume = oswl.resource_data['current'][0]
                self.assertEqual(fv[gt_field_pos],
                                 len(volume['attachments']) > csv_att_num)

    def test_oswl_invalid_data(self):
        exporter = OswlStatsToCsv()
        num = 10
        for resource_type in self.RESOURCE_TYPES:
            oswls_saved = self.get_saved_oswls(
                num, resource_type, current_num_range=(1, 1),
                removed_num_range=(0, 0), added_num_range=(0, 0),
                modified_num_range=(0, 0))
            # Saving installation structures for proper oswls filtering
            self.get_saved_inst_structs(oswls_saved)

            with app.test_request_context():
                oswls = get_oswls(resource_type)
                oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
                    exporter.get_resource_keys_paths(resource_type)

                side_effect = [[]] * num
                side_effect[num / 2] = Exception
                with mock.patch.object(exporter,
                                       'get_additional_resource_info',
                                       side_effect=side_effect):
                    flatten_resources = exporter.get_flatten_resources(
                        resource_type, oswl_keys_paths, vm_keys_paths,
                        oswls, {})
                    # Checking only invalid data is not exported
                    self.assertEqual(num - 1, len(list(flatten_resources)))

    def test_volume_host_not_in_keys_paths(self):
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.volume
        oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
            exporter.get_resource_keys_paths(resource_type)
        self.assertNotIn(['volume', 'host'], csv_keys_paths)

    def test_is_filtered_oswls_export(self):
        for resource_type in self.RESOURCE_TYPES:
            # Creating filtered OSWLs
            filtered_num = 15
            filtered_oswls = self.get_saved_oswls(
                filtered_num,
                resource_type, current_num_range=(1, 1))
            self.get_saved_inst_structs(filtered_oswls,
                                        is_filtered_values=(True,))
            # Creating not filtered OSWLs
            not_filtered_num = 10
            not_filtered_oswls = self.get_saved_oswls(
                not_filtered_num,
                resource_type, current_num_range=(1, 1))
            self.get_saved_inst_structs(not_filtered_oswls)

            # Checking only not filtered resources fetched
            with app.test_request_context():
                oswls = get_oswls_query(resource_type).all()
                self.assertEqual(not_filtered_num, len(oswls))
                for oswl in oswls:
                    self.assertIn(oswl.is_filtered, (False, None))

    def test_release_info_in_oswl(self):
        exporter = OswlStatsToCsv()
        releases = ('6.0', '6.1', None)
        num = 30

        for resource_type in self.RESOURCE_TYPES:
            # Creating  OSWLs
            oswls = self.get_saved_oswls(num, resource_type)
            self.get_saved_inst_structs(oswls, releases=releases)

            with app.test_request_context():
                oswls = get_oswls_query(resource_type).all()
                oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
                    exporter.get_resource_keys_paths(resource_type)

                # Checking release value in flatten resources
                release_pos = csv_keys_paths.index(
                    ['version_info', 'fuel_version'])
                flatten_resources = exporter.get_flatten_resources(
                    resource_type, oswl_keys_paths, resource_keys_paths,
                    oswls, {})
                for flatten_resource in flatten_resources:
                    release = flatten_resource[release_pos]
                    self.assertIn(release, releases)

    def test_duplicated_oswls_skipped(self):
        exporter = OswlStatsToCsv()
        # Creating oswls duplicates
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        old_days = 7
        new_days = 2
        old_created_date = datetime.utcnow().date() - timedelta(days=old_days)
        oswls_saved = [
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=1,
                cluster_id=1,
                created_date=old_created_date,
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='checksum',
                resource_data={'current': [{'id': 1}], 'added': [{'id': 1}]}
            ),
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=2,
                cluster_id=1,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=new_days)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='checksum',
                resource_data={'current': [{'id': 1}], 'added': [{'id': 1}]}
            ),
        ]
        for oswl in oswls_saved:
            db.session.add(oswl)
        self.get_saved_inst_structs(oswls_saved, creation_date_range=(0, 0))

        with app.test_request_context():
            oswls = get_oswls(resource_type)
        oswls_seamless = list(exporter.fill_date_gaps(
            oswls, datetime.utcnow().date()))

        # Checking size of seamless report
        expected_num = old_days + 1  # current date should be in report
        actual_num = len(oswls_seamless)
        self.assertEqual(expected_num, actual_num)

        # Checking only old oswl in seamless_oswls
        for o in oswls_seamless:
            self.assertEqual(old_created_date, o.created_date)

    def test_version_info_in_flatten_resource(self):
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        oswls_saved = [
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=1,
                cluster_id=1,
                created_date=datetime.utcnow().date(),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='no_version_info',
                resource_data={'current': [{'id': 1}]}
            ),
            OpenStackWorkloadStats(
                master_node_uid='y',
                external_id=2,
                cluster_id=2,
                created_date=datetime.utcnow().date(),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='empty_version_info',
                resource_data={'current': [{'id': 1}]},
                version_info={}
            ),
            OpenStackWorkloadStats(
                master_node_uid='z',
                external_id=3,
                cluster_id=3,
                created_date=datetime.utcnow().date(),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='with_version_info',
                resource_data={'current': [{'id': 1}]},
                version_info={
                    'release_version': 'liberty-9.0',
                    'release_os': 'Ubuntu',
                    'release_name': 'Liberty on Ubuntu 14.04',
                    'fuel_version': '9.0',
                    'environment_version': '9.0'
                }
            ),
        ]
        for oswl in oswls_saved:
            db.session.add(oswl)
        self.get_saved_inst_structs(oswls_saved, creation_date_range=(0, 0))

        with app.test_request_context():
            oswls = list(get_oswls(resource_type))

        oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
            exporter.get_resource_keys_paths(resource_type)
        fuel_release_pos = csv_keys_paths.index(
            ['version_info', 'fuel_version'])
        flatten_resources = list(exporter.get_flatten_resources(
            resource_type, oswl_keys_paths, resource_keys_paths, oswls, {}))

        # Checking all oswls are in flatten resources
        external_uid_pos = csv_keys_paths.index(['master_node_uid'])
        expected_uids = set([oswl.master_node_uid for oswl in oswls])
        actual_uids = set([d[external_uid_pos] for d in flatten_resources])
        self.assertEqual(expected_uids, actual_uids)

        # Checking every flatten_resources contain fuel_release_info
        self.assertTrue(all(d[fuel_release_pos] for d in flatten_resources))

    def test_all_resource_statuses_are_shown(self):
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        updated_time_str = datetime.utcnow().time().isoformat()
        oswls_saved = [
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=1,
                cluster_id=1,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=8)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='checksum',
                resource_data={'current': [{'id': 1, 'status': 'enabled',
                                            'tenant_id': 'first'}],
                               'added': [{'id': 1, 'time': updated_time_str}],
                               'modified': [], 'removed': []}
            ),
            # Removing and adding back the same resource.
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=2,
                cluster_id=1,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=6)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='checksum',
                resource_data={
                    'current': [{'id': 1, 'status': 'enabled',
                                 'tenant_id': 'second'}],
                    'added': [{'id': 1, 'time': updated_time_str}],
                    'modified': [],
                    'removed': [{'id': 1, 'status': 'enabled',
                                 'time': updated_time_str,
                                 'tenant_id': 'second'}]}
            ),
            # Changing and restoring back resource
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=3,
                cluster_id=1,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=4)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='checksum',
                resource_data={
                    'current': [{'id': 1, 'enabled': True,
                                 'tenant_id': 'third'}],
                    'added': [],
                    'modified': [
                        {'id': 1, 'enabled': False, 'time': updated_time_str},
                        {'id': 1, 'enabled': True, 'time': updated_time_str},
                    ],
                    'removed': []
                }
            ),
            # Resource modified and finally deleted
            OpenStackWorkloadStats(
                master_node_uid='x',
                external_id=4,
                cluster_id=1,
                created_date=(datetime.utcnow().date() -
                              timedelta(days=2)),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='another_checksum',
                resource_data={
                    'current': [],
                    'added': [],
                    'modified': [
                        {'id': 1, 'enabled': False, 'time': updated_time_str},
                        {'id': 1, 'enabled': True, 'time': updated_time_str},
                    ],
                    'removed': [{'id': 1, 'enabled': True,
                                 'tenant_id': 'fourth'}]
                }
            ),
        ]
        for oswl in oswls_saved:
            db.session.add(oswl)
        self.get_saved_inst_structs(oswls_saved, creation_date_range=(0, 0))

        with app.test_request_context():
            oswls = get_oswls(resource_type)

        oswls_seamless = list(exporter.fill_date_gaps(
            oswls, datetime.utcnow().date()))

        oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
            exporter.get_resource_keys_paths(resource_type)

        flatten_resources = list(exporter.get_flatten_resources(
            resource_type, oswl_keys_paths, resource_keys_paths,
            oswls_seamless, {}))

        # Expected oswls num: 2 for 'first', 2 for 'second', 2 for 'third'
        # and only one for finally removed 'fourth'
        expected_oswls_num = 7
        self.assertEqual(expected_oswls_num, len(flatten_resources))

        is_added_pos = csv_keys_paths.index([resource_type, 'is_added'])
        is_modified_pos = csv_keys_paths.index([resource_type, 'is_modified'])
        is_removed_pos = csv_keys_paths.index([resource_type, 'is_removed'])
        tenant_id_pos = csv_keys_paths.index([resource_type, 'tenant_id'])

        def check_resource_state(resource, tenant_id, is_added,
                                 is_modified, is_removed):
            self.assertEquals(is_added, resource[is_added_pos])
            self.assertEquals(is_modified, resource[is_modified_pos])
            self.assertEquals(is_removed, resource[is_removed_pos])
            self.assertEquals(tenant_id, resource[tenant_id_pos])

        # The fist oswl status True only in is_added
        check_resource_state(flatten_resources[0], 'first',
                             True, False, False)

        # The first oswl status on the next day is False for
        # is_added, is_modified, is_removed
        check_resource_state(flatten_resources[1], 'first',
                             False, False, False)

        # The second oswl status True in is_added, is_modified
        check_resource_state(flatten_resources[2], 'second',
                             True, False, True)

        # The second oswl status on the next day is False for
        # is_added, is_modified, is_removed
        check_resource_state(flatten_resources[3], 'second',
                             False, False, False)

        # The third oswl status True only in is_modified
        check_resource_state(flatten_resources[4], 'third',
                             False, True, False)

        # The third oswl status on the next day is False for
        # is_added, is_modified, is_removed
        check_resource_state(flatten_resources[5], 'third',
                             False, False, False)

        # The fourth oswl status True in is_modified, is_deleted
        check_resource_state(flatten_resources[6], 'fourth',
                             False, True, True)

    def test_fuel_version_from_clusters_data_is_used(self):
        master_node_uid = 'x'
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        version_from_cluster = '7.0'
        release_version_from_cluster = 'from_cluster_7.0'
        version_from_version_info = '9.0'
        release_version_from_version_info = 'from_version_info_9.0'

        version_from_installation_info = '8.0'
        release_version_from_inst_info = 'from_inst_info_8.0'
        installation_date = datetime.utcnow().date() - timedelta(days=3)

        # Upgraded Fuel and not upgraded cluster
        structure = InstallationStructure(
            master_node_uid=master_node_uid,
            structure={
                'fuel_release': {
                    'release': version_from_installation_info,
                    'openstack_version': release_version_from_inst_info
                },
                'clusters_num': 2,
                'clusters': [
                    {'id': 1, 'fuel_version': version_from_cluster,
                     'release': {'version': release_version_from_cluster}},
                    {'id': 2}
                ],
                'unallocated_nodes_num_range': 0,
                'allocated_nodes_num': 0
            },
            creation_date=installation_date,
            is_filtered=False
        )
        db.session.add(structure)

        oswls = [
            OpenStackWorkloadStats(
                master_node_uid=master_node_uid,
                external_id=1,
                cluster_id=1,
                created_date=installation_date,
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='info_from_cluster',
                resource_data={'current': [{'id': 1, 'status': 'enabled'}],
                               'added': [], 'modified': [], 'removed': []},
                version_info=None
            ),
            OpenStackWorkloadStats(
                master_node_uid=master_node_uid,
                external_id=3,
                cluster_id=1,
                created_date=installation_date + timedelta(days=1),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='info_from_version_info',
                resource_data={'current': [{'id': 1}],
                               'added': [], 'modified': [], 'removed': []},
                version_info={
                    'fuel_version': version_from_version_info,
                    'release_version': release_version_from_version_info
                }
            ),
            OpenStackWorkloadStats(
                master_node_uid=master_node_uid,
                external_id=2,
                cluster_id=2,
                created_date=installation_date + timedelta(days=2),
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='info_from_installation_info',
                resource_data={'current': [{'id': 1}],
                               'added': [], 'modified': [], 'removed': []},
                version_info=None
            )
        ]
        for oswl in oswls:
            db.session.add(oswl)

        with app.test_request_context():
            oswls_data = list(get_oswls(resource_type))
            clusters_version_info = get_clusters_version_info()

        oswl_keys_paths, resource_keys_paths, csv_keys_paths = \
            exporter.get_resource_keys_paths(resource_type)
        fuel_release_pos = csv_keys_paths.index(
            ['version_info', 'fuel_version'])
        release_version_pos = csv_keys_paths.index(
            ['version_info', 'release_version'])
        flatten_resources = list(exporter.get_flatten_resources(
            resource_type, oswl_keys_paths,
            resource_keys_paths, oswls_data, clusters_version_info
        ))

        self.assertEqual(len(oswls), len(flatten_resources))

        # Checking version info fetched from cluster
        self.assertEqual(version_from_cluster,
                         flatten_resources[0][fuel_release_pos])
        self.assertEqual(release_version_from_cluster,
                         flatten_resources[0][release_version_pos])

        # Checking version info fetched from oswl.version_info
        self.assertEqual(version_from_version_info,
                         flatten_resources[1][fuel_release_pos])
        self.assertEqual(release_version_from_version_info,
                         flatten_resources[1][release_version_pos])

        # Checking version info fetched from installation info
        self.assertEqual(version_from_installation_info,
                         flatten_resources[2][fuel_release_pos])
        self.assertEqual(release_version_from_inst_info,
                         flatten_resources[2][release_version_pos])

    def test_get_clusters_version_info(self):
        mn_uid = 'x'
        cluster_id = 1
        empty_cluster_id = 2
        mn_uid_no_clusters = 'xx'
        release_name = 'release name'
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        version_from_cluster = '7.0'
        release_version_from_cluster = 'from_cluster_7.0'
        installation_date = datetime.utcnow().date() - timedelta(days=3)

        expected_version_info = {
            'release_version': release_version_from_cluster,
            'release_os': None,
            'release_name': release_name,
            'fuel_version': version_from_cluster
        }

        structures = [
            InstallationStructure(
                master_node_uid=mn_uid,
                structure={
                    'clusters': [
                        {'id': cluster_id,
                         'fuel_version': version_from_cluster,
                         'release': {'version': release_version_from_cluster,
                                     'name': release_name}},
                        {'id': empty_cluster_id}
                    ]

                },
                creation_date=installation_date,
                is_filtered=False
            ),
            InstallationStructure(
                master_node_uid=mn_uid_no_clusters,
                structure={'clusters': []},
                creation_date=installation_date,
                is_filtered=False
            )
        ]
        for structure in structures:
            db.session.add(structure)

        oswls = [
            OpenStackWorkloadStats(
                master_node_uid=mn_uid,
                external_id=1,
                cluster_id=1,
                created_date=installation_date,
                updated_time=datetime.utcnow().time(),
                resource_type=resource_type,
                resource_checksum='info_from_cluster',
                resource_data={'current': [{'id': 1, 'status': 'enabled'}],
                               'added': [], 'modified': [], 'removed': []},
                version_info=None
            )
        ]
        for oswl in oswls:
            db.session.add(oswl)

        with app.test_request_context():
            clusters_version_info = get_clusters_version_info()

        self.assertIn(mn_uid, clusters_version_info)
        self.assertIn(cluster_id, clusters_version_info[mn_uid])
        self.assertNotIn(empty_cluster_id, clusters_version_info[mn_uid])
        self.assertIn(mn_uid_no_clusters, clusters_version_info)

        actual_version_info = clusters_version_info[mn_uid][cluster_id]
        self.assertEqual(expected_version_info, actual_version_info)
        self.assertEqual({}, clusters_version_info[mn_uid_no_clusters])
