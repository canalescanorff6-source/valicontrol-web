#!/usr/bin/env bash
set -o errexit
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py init_db
python manage.py indexar_catalogo --skip-if-ready || true
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-2} --timeout 120 --access-logfile - --error-logfile -
