#    Copyright 2016 Mirantis, Inc.
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
from datetime import date
from datetime import datetime

import json_delta
import six

from collector.api.app import app
from collector.api.app import db
from collector.api.db import model


def get_resource_id(obj, resource_ids_names):
    ids = (getattr(obj, name) for name in resource_ids_names)
    return ','.join(six.moves.map(six.text_type, ids))


def write_history(obj, version_tag=None, exclude_fields=('id',),
                  resource_type_getter=lambda x: x.__tablename__,
                  resource_ids_names=('id',)):
    resource_id = get_resource_id(obj, resource_ids_names)
    resource_type = resource_type_getter(obj)
    current_data = obj_to_dict(obj, exclude_fields=exclude_fields)

    app.logger.debug("Writing history for resource %s with id %s. "
                     "Current data: %s", resource_type, resource_id,
                     current_data)

    last_snapshot = db.session.query(model.HistoryLastSnapshot).filter(
        resource_id == resource_id, resource_type == resource_type).first()

    if last_snapshot is None:
        app.logger.debug("Last snapshot doesn't found for resource %s "
                         "with id: %s", resource_type, resource_id)
        db.session.add(model.HistoryLastSnapshot(
            resource_id=resource_id,
            resource_type=resource_type,
            created=datetime.utcnow(),
            data=current_data
        ))
        app.logger.debug("Last snapshot saved for resource %s with id %s",
                         resource_type, resource_id)
    else:
        app.logger.debug("Last snapshot found %s for resource %s with id %s",
                         last_snapshot.id, resource_type, resource_id)

        diff = json_delta.diff(current_data, last_snapshot.data)
        if not diff:
            app.logger.debug("Differences don't found between last snapshot "
                             "and current data for resource %s with id %s",
                             resource_type, resource_id)
            return

        app.logger.debug("Differences between last snapshot and current data "
                         "saved for resource %s with id %s: %s",
                         resource_type, resource_id, diff)

        version_tag = version_tag or model.version_tag_seq.next_value()
        created = copy.copy(last_snapshot.created)
        db.session.add(model.History(
            resource_id=resource_id,
            resource_type=resource_type,
            version_tag=version_tag,
            created=created,
            data_diff=diff
        ))
        last_snapshot.created = datetime.utcnow()
        last_snapshot.data = current_data

        app.logger.debug("Differences between last snapshot and current data "
                         "saved for resource %s with id %s: %s",
                         resource_type, resource_id, diff)


def obj_to_dict(obj, exclude_fields=()):
    """Converts collector.api.db.model instance to dict."""
    result = {}
    for column in obj.__table__.columns:
        name = column.name
        if name in exclude_fields:
            continue
        value = getattr(obj, name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        result[name] = value
    return result
