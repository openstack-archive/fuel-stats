==========
Fuel stats
==========

Project purpose
---------------

* collects stats information about OpenStack installations made by Fuel_,
* generates stat reports in the CSV format,
* provides API for fetching raw data in the JSON format,
* provides Web UI for reports generation and basic stats charts/histograms.

Components
----------

Collector is the service for collecting stats. It has REST API and DB storage.
Analytics is the service for generating reports. It has REST API.
Migrator is the tool for migrating data from the DB to the Elasticsearch_.

The collector and analytics services are started by uWSGI_. Migrator is
started by cron to migrate the fresh data into Elasticsearch_.

Collector
---------

Data origin for collector is the Fuel_ master node. Stats collecting daemons
collect and send data to the collector if allowed by the cloud operator.

Stats data is stored to the DB PostgreSQL_.

Migrator
--------

Migrator periodically migrates data from the fuel-stats DB to the
Elasticsearch_ storage. This storage is used to generate basic stats charts
and histograms for the Web UI.

Analytics
---------

There are two sub-components in the analytics:

* analytics service
* Web UI

The analytics service API provides generation of CSV reports for installation
info, plugins, and OpenStack workloads. The analytics API also provides
export of data from DB as JSON.

The analytics Web UI provides basic summary stats charts and histograms with
the possibility of filtering data by the Fuel_ release version. Also, in the
Web UI we can generate and download stats reports on a selected time period.

.. _howto configure dev environment:

How to configure development environment
----------------------------------------

To start fuel-stats on a localhost we need to have:

* PostgreSQL_ of version 9.3 or greater,
* Elasticsearch_ of version 1.3.4 or greater,
* Nginx_.

Install PostgreSQL_ and development libraries: ::

  sudo apt-get install --yes postgresql postgresql-server-dev-all

Configure Elasticsearch_ repo as described in the `elasticsearch docs`_ and
install Elasticsearch_:::

  sudo apt-get install --yes elasticsearch

Install pip and development tools: ::

  sudo apt-get install --yes python-dev python-pip

Install virtualenv. This step increases flexibility when dealing with
environment settings and package installation: ::

  sudo pip install virtualenv virtualenvwrapper

You can add '. /usr/local/bin/virtualenvwrapper.sh' to .bashrc or just
execute it.::

  . /usr/local/bin/virtualenvwrapper.sh

Create and activate virtual env for fuel-stats: ::

  mkvirtualenv stats
  workon stats

You can use any name for the virtual env instead of 'stats'.

Install the fuel-stats requirements: ::

  pip install -r test-requirements.txt

Create a DB user for fuel-stats: ::

  sudo -u postgres psql
  CREATE ROLE collector WITH NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN ENCRYPTED PASSWORD 'collector';

Create a DB and grant privileges to it: ::

  sudo -u postgres psql
  CREATE DATABASE collector;
  GRANT ALL ON DATABASE collector TO collector;

Check that all tests are passed: ::

  cd fuel-stats/collector && tox
  cd fuel-stats/migration && tox
  cd fuel-stats/analytics && tox

**NOTE:** The collector tests must be performed the first.

Now you are ready to develop fuel-stats.

How to configure Web UI
-----------------------

We assume that you already have configured virtual env as described in
`howto configure dev environment`_.

Install elsticsearch library and create sample data: ::

  workon stats
  pip install elasticsearch
  cd migration
  nosetests migration.test.report.test_reports:Reports.test_libvirt_type_distribution

Install nodejs: ::

  sudo apt-get remove nodejs nodejs-legacy npm
  sudo add-apt-repository -y ppa:chris-lea/node.js
  sudo apt-get update
  sudo apt-get install nodejs

Install nodejs and bower packages: ::

  cd fuel-stats/analytics/static
  npm install
  gulp bower

You can anytime lint your code by running: ::

  gulp lint

Add site configuration to Nginx_: ::

    server {
        listen 8888;
        location / {
            root /your-path-to-fuel-stats/fuel-stats/analytics/static;
        }
        location ~ ^(/fuel)?(/[A-Za-z_0-9])?/(_count|_search) {
            proxy_pass http://127.0.0.1:9200;
        }
    }

Then restart Nginx: ::

  service nginx restart

After this, your local server will be available at 0.0.0.0:8888
or any other port you've set up.

How to start local collector
----------------------------

You can use uWSGI_ to start the collector. Sample config can be found in
collector/uwsgi/collector_example.yaml.

Or test web service to be used. To start the test web service, run: ::

  python collector/manage_collector.py --mode test runserver

How to start local analytics
----------------------------

You can use uWSGI_ to start analytics. Sample config can be found in
analytics/uwsgi/analytics_example.yaml.

Or test the web service to be used. To start the test web service, run: ::

  python analytics/manage_analytics.py --mode test runserver

How to deal with DB migrations
------------------------------

Create new DB migration: ::

  python manage_collector.py --mode test db migrate -m "Migration comment" \
  -d collector/api/db/migrations/

Apply all DB migrations: ::

  python manage_collector.py --mode test db upgrade -d collector/api/db/migrations/

Revert all migrations: ::

  python manage_collector.py --mode test db downgrade -d collector/api/db/migrations/


Switching off Elasticsearch
---------------------------

Elasticsearch was chosen as data storage for the dynamically generated
statistics reports, but now only CSV reports are used for analytical purposes.
Thus, Elasticsearch is an unnecessary complication of the infrastructure and
data flow.

Without Elasticsearch, we are using memcached as cache for the web UI. Data
expiration is configured by the parameter MEMCACHED_JSON_REPORTS_EXPIRATION
for fuel_analytics.

Changes in the Nginx config: ::

    # Add this to the block 'server'
    location /api/ {
        proxy_pass http://IP_OF_ANALYTICS_SERVICE:PORT_OF_ANALYTICS_SERVICE/api/;
    }


.. _Fuel: https://docs.mirantis.com/openstack/fuel/
.. _Elasticsearch: https://www.elastic.co/
.. _uWSGI: https://pypi.python.org/pypi/uWSGI/
.. _PostgreSQL: http://www.postgresql.org/
.. _Nginx: http://nginx.org/
.. _elasticsearch docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/setup-repositories.html
