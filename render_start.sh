#!/usr/bin/env bash
set -euo pipefail

echo "[render_start] Running Django migrations..."
python manage.py migrate --noinput

echo "[render_start] Collecting static files..."
python manage.py collectstatic --noinput

# OPTIONAL: Crear superusuario automático una sola vez (después borrar)
# python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" || true

echo "[render_start] Starting Gunicorn on port ${PORT}"
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3
