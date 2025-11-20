#!/usr/bin/env bash
set -euo pipefail

# Helper entrypoint for Render cuando usas SQLite.
# Asegura que el archivo sqlite existe y es escribible, corre migraciones y arranca gunicorn.

# Localización del archivo DB: lee de DATABASE_URL o usa db.sqlite3 en el project root
if [ -n "${DATABASE_URL-}" ] && [[ "$DATABASE_URL" == sqlite:* ]]; then
  # soporte para sqlite:///db.sqlite3 (relativo) y sqlite:////tmp/db.sqlite3 (absoluto)
  if [[ "$DATABASE_URL" == sqlite:////* ]]; then
    DB_PATH="${DATABASE_URL#sqlite:}"
  else
    # remueve el esquema y las barras extras
    RAW_PATH="${DATABASE_URL#sqlite:////}"
    RAW_PATH="${RAW_PATH#///}"
    DB_PATH="$(pwd)/${RAW_PATH:-db.sqlite3}"
  fi
else
  DB_PATH="$(pwd)/db.sqlite3"
fi

echo "[render_start] using sqlite path: $DB_PATH"

# Asegura el directorio
mkdir -p "$(dirname "$DB_PATH")"

# Crea el archivo si no existe y da permisos para que render pueda escribir
if [ ! -f "$DB_PATH" ]; then
  echo "[render_start] creating sqlite file: $DB_PATH"
  touch "$DB_PATH"
fi
chmod 666 "$DB_PATH" || true

echo "[render_start] running migrations"
python manage.py migrate --no-input || true

# Seed inicial solo si la variable está activa
if [ "${SEED_INITIAL_DATA:-}" = "1" ] || [ "${SEED_INITIAL_DATA:-}" = "true" ]; then
  echo "[render_start] seeding initial data"
  python manage.py seed_initial_data || true
fi

echo "[render_start] PORT=${PORT:-<not set>}"

# Arranca Gunicorn (última línea! Render espera el proceso activo aquí)
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 3
