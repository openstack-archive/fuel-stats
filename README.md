collector
=========

Prototype of statistic collector

Operations
----------


Install requirements:

`pip install -r test-requirements.txt`

By default manage.py works with test settings.
For working with prod settings use `python manage.py --mode` option.

For creating DB migration:

`python manage.py db migrate -m "Migration comment" \
-d collector/api/db/migrations/`

Create DB user with password 'collector':

`sudo -u postgres createuser -DES collector`

or

`sudo -u postgres psql
> CREATE ROLE collector WITH NOSUPERUSER NOCREATEDB NOCREATEROLE ENCRYPTED PASSWORD 'colector';
`

Create DB and grant privileges to it:

`sudo -u postgres psql
> CREATE DATABASE collector;
> GRANT ALL ON DATABASE collector TO collector;`

For apply the latest migration:

`python manage.py db upgrade -d collector/api/db/migrations/`

For revert all migrations:

`python manage.py db downgrade -d collector/api/db/migrations/`

For starting test server:

`python manage.py runserver`
