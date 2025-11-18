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
# Run migrations at start (safer to run when runtime DB is available)
echo "[render_start] running migrations"
python manage.py migrate --no-input || true

# Optionally seed initial data if SEED_INITIAL_DATA env var is set to 1/true
if [ "${SEED_INITIAL_DATA:-}" = "1" ] || [ "${SEED_INITIAL_DATA:-}" = "true" ]; then
  echo "[render_start] seeding initial data"
  python manage.py seed_initial_data || true
fi

  # Log PORT value for debugging (Render sets this at runtime)
  echo "[render_start] PORT=${PORT:-<not set>}"

  # Use PORT provided by Render. When running on Render the environment variable
  # `PORT` should be set by the platform. We still support a local fallback for
  # development but prefer the platform-provided value.
  exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
