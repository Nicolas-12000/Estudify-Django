#!/usr/bin/env bash
set -euo pipefail

echo "[render_start] running migrations"
python manage.py migrate --no-input || true

echo "[render_start] creating default admin if not exists"
python manage.py shell -c "from create_default_admin import create_default_admin; create_default_admin()" || true

echo "[render_start] starting server"
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
