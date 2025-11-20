#!/usr/bin/env bash
set -euo pipefail

echo "[render_start] running migrations"
python manage.py migrate --no-input

echo "[render_start] Creando superusuario si no existe..."
python manage.py createsuperuser --noinput || true

echo "[render_start] Arrancando Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
