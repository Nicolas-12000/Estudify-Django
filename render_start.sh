#!/usr/bin/env bash
set -euo pipefail

echo "[render_start] running migrations"
python manage.py migrate --no-input

echo "[render_start] collect static"
python manage.py collectstatic --no-input

echo "[render_start] creating default admin if not exists"
python manage.py create_default_admin

echo "[render_start] starting server"
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
