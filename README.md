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

`python manage.py db migrate -m "Migration comment"
-d collector/api/db/migrations/`

For starting test server:

`python manage.py runserver`
