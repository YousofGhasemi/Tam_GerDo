#!/bin/sh

set -e

export DJANGO_SETTINGS_MODULE=app.settings
export PYTHONPATH=/app:$PYTHONPATH

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate



uwsgi --chdir /app --pythonpath /app --module app.wsgi:application --socket :9000 --workers 4 --master --enable-threads