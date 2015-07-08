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
import flask
import mock
import six
import types
import uuid

from fuel_analytics.test.api.resources.utils.oswl_test import OswlTest
from fuel_analytics.test.base import DbTest

from fuel_analytics.api.app import app
from fuel_analytics.api.app import db
from fuel_analytics.api.common import consts
from fuel_analytics.api.db.model import OpenStackWorkloadStats
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
            self.assertIn(['release'], oswl_keys_paths)
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
                resource_type, oswl_keys_paths, resource_keys_paths, oswls)
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
            resource_type, oswl_keys_paths, resource_keys_paths, oswls)

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
                result = exporter.export(resource_type, oswls,
                                         datetime.utcnow().date())
                self.assertTrue(isinstance(result, types.GeneratorType))
                output = six.StringIO(list(result))
                reader = csv.reader(output)
                for _ in reader:
                    pass

    def test_export_on_empty_data(self):
        exporter = OswlStatsToCsv()
        for resource_type in self.RESOURCE_TYPES:
            result = exporter.export(resource_type, [], None)
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
        with app.test_request_context(), mock.patch.object(
                flask.request, 'args', {'from_date': '2015-02-01'}):
            for resource_type in self.RESOURCE_TYPES:
                # Creating oswls
                oswls_saved = self.get_saved_oswls(num, resource_type)
                self.get_saved_inst_structs(oswls_saved)
                # Filtering oswls
                oswls = get_oswls(resource_type)
                result = exporter.export(resource_type, oswls,
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

        with app.test_request_context():
            with mock.patch.object(
                flask.request,
                'args',
                {
                    'from_date': (base_date - timedelta(days=2)).isoformat(),
                    'to_date': (base_date - timedelta(days=1)).isoformat()
                }
            ):
                oswls = list(get_oswls(resource_type))
                self.assertEqual(0, len(oswls))
                result = exporter.export(
                    resource_type,
                    oswls,
                    (base_date - timedelta(days=1))
                )
                # Only column names in result
                self.assertEqual(1, len(list(result)))
            with mock.patch.object(
                flask.request,
                'args',
                {
                    'to_date': (base_date - timedelta(days=1)).isoformat()
                }
            ):
                oswls = list(get_oswls(resource_type))
                self.assertEqual(0, len(oswls))
                result = exporter.export(
                    resource_type,
                    oswls,
                    base_date - timedelta(days=1)
                )
                # Only column names in result
                self.assertEqual(1, len(list(result)))
            with mock.patch.object(
                flask.request,
                'args',
                {
                    'to_date': base_date.isoformat()
                }
            ):
                oswls = list(get_oswls(resource_type))
                self.assertEqual(1, len(oswls))
                result = exporter.export(
                    resource_type,
                    oswls,
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

            oswls = list(get_oswls(resource_type).all())
            oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
                exporter.get_resource_keys_paths(resource_type)
            flatten_volumes = exporter.get_flatten_resources(
                resource_type, oswl_keys_paths, vm_keys_paths, oswls)
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
                oswls = get_oswls(resource_type).all()
                oswl_keys_paths, vm_keys_paths, csv_keys_paths = \
                    exporter.get_resource_keys_paths(resource_type)

                side_effect = [[]] * num
                side_effect[num / 2] = Exception
                with mock.patch.object(exporter,
                                       'get_additional_resource_info',
                                       side_effect=side_effect):
                    flatten_resources = exporter.get_flatten_resources(
                        resource_type, oswl_keys_paths, vm_keys_paths, oswls)
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
                release_pos = csv_keys_paths.index(['release'])
                flatten_resources = exporter.get_flatten_resources(
                    resource_type, oswl_keys_paths, resource_keys_paths, oswls)
                for flatten_resource in flatten_resources:
                    release = flatten_resource[release_pos]
                    self.assertIn(release, releases)
