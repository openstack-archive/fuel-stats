collector
=========

Prototype of statistic collector

Operations
----------


Install requirements:

    pip install -r test-requirements.txt

By default manage_collector.py works with prod settings.
For working with test settings use `python manage_collector.py --mode` option.

For creating DB migration:

    python manage_collector.py --mode test db migrate -m "Migration comment" \
    -d collector/api/db/migrations/

Create DB user with password 'collector':

    sudo -u postgres createuser -DES collector

or:

    sudo -u postgres psql
    CREATE ROLE collector WITH NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN ENCRYPTED PASSWORD 'collector';

Create DB and grant privileges to it:

    sudo -u postgres psql
    CREATE DATABASE collector;
    GRANT ALL ON DATABASE collector TO collector;

For apply the latest migration:

    python manage_collector.py --mode test db upgrade -d collector/api/db/migrations/

For revert all migrations:

    python manage_collector.py --mode test db downgrade -d collector/api/db/migrations/

For starting test server:

    python manage_collector.py --mode test runserver

Example config for uWSGI is located in collector/uwsgi/collector_test.yaml
