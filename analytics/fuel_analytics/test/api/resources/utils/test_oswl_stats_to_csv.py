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
            self.assertFalse(['external_id'] in oswl_keys_paths)
            self.assertFalse(['updated_time'] in oswl_keys_paths)
            self.assertTrue([resource_type, 'id'] in resource_keys_paths)
            self.assertTrue([resource_type, 'is_added'] in csv_keys_paths)
            self.assertTrue([resource_type, 'is_modified'] in csv_keys_paths)
            self.assertTrue([resource_type, 'is_removed'] in csv_keys_paths)

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
            db.session.commit()
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
                actual = exporter.get_additional_resource_info(resource, oswl)
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
            db.session.commit()

            oswls = get_oswls_query(resource_type).all()
            oswl = oswls[0]
            self.assertEquals(
                inst_struct.creation_date,
                exporter.get_last_sync_datetime(oswl)
            )

            inst_struct.modification_date = datetime.utcnow()
            db.session.commit()
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
            db.session.commit()
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
            db.session.commit()

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
                db.session.commit()
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
        db.session.commit()

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
        exporter = OswlStatsToCsv()
        resource_type = consts.OSWL_RESOURCE_TYPES.vm
        oswl = OpenStackWorkloadStats(
            master_node_uid='x',
            external_id=1,
            cluster_id=1,
            created_date=datetime(2015, 2, 23).date(),
            updated_time=datetime.utcnow().time(),
            resource_type=resource_type,
            resource_checksum='',
            resource_data={'current': [{'id': 444, 'status': 'ACTIVE'}]}
        )
        db.session.add(oswl)
        self.get_saved_inst_structs([oswl], creation_date_range=(0, 0))
        db.session.commit()

        with app.test_request_context():
            with mock.patch.object(flask.request, 'args',
                                   {'from_date': '2015-02-21',
                                    'to_date': '2015-02-22'}):
                oswls = list(get_oswls(resource_type))
                self.assertEqual(0, len(oswls))
                result = exporter.export(resource_type, oswls,
                                         datetime(2015, 2, 22).date())
                # Only column names in result
                self.assertEqual(1, len(list(result)))
            with mock.patch.object(flask.request, 'args',
                                   {'to_date': '2015-02-22'}):
                oswls = list(get_oswls(resource_type))
                self.assertEqual(0, len(oswls))
                result = exporter.export(resource_type, oswls,
                                         datetime(2015, 2, 22).date())
                # Only column names in result
                self.assertEqual(1, len(list(result)))
            with mock.patch.object(flask.request, 'args',
                                   {'to_date': '2015-02-24'}):
                oswls = list(get_oswls(resource_type))
                self.assertEqual(1, len(oswls))
                result = exporter.export(resource_type, oswls,
                                         datetime(2015, 2, 24).date())
                # Not only column names in result
                self.assertEqual(1 + 2, len(list(result)))

    def test_resource_data_structure(self):
        num = 20
        for resource_type in self.RESOURCE_TYPES:
            oswls = self.get_saved_oswls(num, resource_type)
            for oswl in oswls:
                for res_data in oswl.resource_data['current']:
                    self.assertItemsEqual(
                        six.iterkeys(OSWL_SKELETONS[resource_type]),
                        six.iterkeys(res_data)
                    )
