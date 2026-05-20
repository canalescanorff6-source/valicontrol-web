#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
python manage.py migrate --noinput
python manage.py init_db
python manage.py indexar_catalogo --skip-if-ready || true
