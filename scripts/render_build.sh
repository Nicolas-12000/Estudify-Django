#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build de Estudify (Render) ..."

# Use python -m pip for better portability
echo "📦 Actualizando pip e instalando dependencias..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Collect static files
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones de base de datos..."
python manage.py migrate --no-input

echo "✅ Build completado exitosamente!"
