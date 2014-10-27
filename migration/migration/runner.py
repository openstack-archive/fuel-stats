#    Copyright 2014 Mirantis, Inc.
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

import time

from migration import config
from migration.log import logger
from migration.migrator import Migrator


def run_forever():
    migrator = Migrator()
    while True:
        logger.info("Migration started")
        start = time.time()
        try:
            migrator.create_indices()
            try:
                migrator.migrate_action_logs()
            except Exception:
                logger.exception("Action logs migration failed")
            try:
                migrator.migrate_installation_structure()
            except Exception:
                logger.exception("Installation structure migration failed")
            logger.info("Migration finished")
        except Exception:
            logger.exception("Indices creation failed")
        end = time.time()
        sleep_for = config.SYNC_EVERY_SECONDS - (start - end)
        if sleep_for > 0:
            logger.info("Going to sleep for %d seconds", sleep_for)
            time.sleep(sleep_for)


def main():
    """Entry point
    """
    run_forever()
