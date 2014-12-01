collector
=========

Prototype of statistic collector

Requirements
----------

System requirements:
postgresql database server of version 9.3 or greater.

To install python requirements use command:
`pip install -r {corresponding_requirement_file}`

Operations
----------

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


Local setup
----------

To run statistics UI locally you need to do the following:

Install elasticsearch 1.3

    pip install elasticsearch

Run test_report from NodesDistribution

    prepare virtualenv:

        cd fuel-stats
        virtualenv .venv
        source .venv/bin/activate
        pip install -r collector/test-requirements.txt
        cd migration

    run tests:

        nosetests migration.test.report.test_reports:Reports.test_libvirt_type_distribution

    or

        nosetests migration.test.report.test_os_distribution:OsDistribution


    this will create demo data from elasticsearch

Install elasticsearch service

    you can use this helpfull gist https://gist.github.com/wingdspur/2026107

And don't forget to start elasticsearch service

    sudo service elasticsearch start

Nginx installation

    sudo apt-get install nginx

    fix Nginx config:

        server {
            listen 8888;       // your free port
            location / {
                root /home/kpimenova/fuel/fuel-stats/analytics/static;    // your path to fuel-stats/analytics/static
            }
            location ~ ^(/fuel)?(/[A-Za-z_0-9])?/(_count|_search) {
                proxy_pass http://127.0.0.1:9200;
            }
        }

Then restart Nginx:

    service nginx restart

 After this your local server will be available at 0.0.0.0:8888 // or any other port you've set up :)


 Also for correct UI work you need to setup a few things

 Install nodejs packages

    cd fuel-stats/analytics/static
    npm install

 Install bower packages

    cd fuel-stats/analytics/static
    gulp bower

 That's all.

 You can anytime lint your code by running

    gulp lint

