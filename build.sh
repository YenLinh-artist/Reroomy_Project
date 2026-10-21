#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput --settings=reroomy_core.settings_staging
python manage.py migrate --noinput --settings=reroomy_core.settings_staging
