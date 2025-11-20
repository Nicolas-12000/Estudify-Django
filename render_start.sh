#!/usr/bin/env bash
set -euo pipefail

echo "[render_start] running migrations"
python manage.py migrate --no-input || true

echo "[render_start] creating default superuser if not exists"
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'Admin123')
    print("Superuser created: admin / Admin123")
else:
    print("Superuser already exists")
EOF

echo "[render_start] starting server"
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
