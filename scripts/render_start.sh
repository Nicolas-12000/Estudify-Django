#!/usr/bin/env bash
set -euo pipefail

# Helper entrypoint for Render when using SQLite during Sprint-0.
# Ensures the sqlite DB file exists and is writable, runs migrations and starts gunicorn.

# Location of DB: read from DATABASE_URL env or fallback to project db.sqlite3
if [ -n "${DATABASE_URL-}" ] && [[ "$DATABASE_URL" == sqlite:* ]]; then
  # support sqlite:///db.sqlite3 (relative) and sqlite:////tmp/db.sqlite3 (absolute)
  if [[ "$DATABASE_URL" == sqlite:////* ]]; then
    DB_PATH="${DATABASE_URL#sqlite:}"
  else
    # remove scheme and leading slashes
    RAW_PATH="${DATABASE_URL#sqlite:////}"
    RAW_PATH="${RAW_PATH#///}"
    # default to project root
    DB_PATH="$(pwd)/${RAW_PATH:-db.sqlite3}"
  fi
else
  DB_PATH="$(pwd)/db.sqlite3"
fi

echo "[render_start] using sqlite path: $DB_PATH"

# ensure directory exists
mkdir -p "$(dirname "$DB_PATH")"

# create file if missing and set permissive permissions so migrations during build can write
if [ ! -f "$DB_PATH" ]; then
  echo "[render_start] creating sqlite file: $DB_PATH"
  touch "$DB_PATH"
fi
chmod 666 "$DB_PATH" || true

echo "[render_start] starting gunicorn (lightweight start, migrations/collectstatic should run during Build)"
# Use PORT provided by Render
exec gunicorn -b 0.0.0.0:${PORT:-10000} config.wsgi:application --workers 3
