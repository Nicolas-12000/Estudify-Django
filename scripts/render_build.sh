#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build de Estudify (Render) ..."

echo "📦 Actualizando pip e instalando dependencias..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "🗄️ Ejecutando migraciones de base de datos..."
python manage.py migrate --no-input

echo "✅ Build completado exitosamente!"
