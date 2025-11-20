#!/usr/bin/env bash
set -euo pipefail

if [ -n "${DATABASE_URL-}" ] && [[ "$DATABASE_URL" == sqlite:* ]]; then
  if [[ "$DATABASE_URL" == sqlite:////* ]]; then
    DB_PATH="${DATABASE_URL#sqlite:}"
  else
    RAW_PATH="${DATABASE_URL#sqlite:////}"
    RAW_PATH="${RAW_PATH#///}"
    DB_PATH="$(pwd)/${RAW_PATH:-db.sqlite3}"
  fi
else
  DB_PATH="$(pwd)/db.sqlite3"
fi

echo "[render_start] using sqlite path: $DB_PATH"
mkdir -p "$(dirname "$DB_PATH")"

if [ ! -f "$DB_PATH" ]; then
  echo "[render_start] creating sqlite file: $DB_PATH"
  touch "$DB_PATH"
fi
chmod 666 "$DB_PATH" || true

echo "[render_start] running migrations"
python manage.py migrate --no-input || true

if [ "${SEED_INITIAL_DATA:-}" = "1" ] || [ "${SEED_INITIAL_DATA:-}" = "true" ]; then
  echo "[render_start] seeding initial data"
  python manage.py seed_initial_data || true
fi

echo "[render_start] PORT=${PORT:-<not set>}"

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
