# Estudify

> Plataforma de gestión académica — Sprint 0: configuración inicial

Este repositorio contiene la base del proyecto Django `Estudify`. El objetivo del Sprint 0 es dejar el proyecto ejecutable localmente, con pruebas básicas, documentación inicial y CI que ejecute los tests.

---

Requisitos
- Python 3.12+
- Git
- Virtualenv (o venv)

Instalación local rápida
1. Clona el repo:

   git clone 
   cd estudify

2. Crea y activa un entorno virtual (Windows PowerShell):

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

3. Instala dependencias:

```powershell
pip install -r requirements.txt
```

4. Copia el ejemplo de variables de entorno y edita `.env`:

```powershell
copy .env.example .env
# Luego edita .env para agregar SECRET_KEY, DEBUG, ALLOWED_HOSTS, etc.
```

5. Ejecuta migraciones y crea superuser:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

6. Ejecuta el servidor:

```powershell
python manage.py runserver
# Visita http://127.0.0.1:8000/
```

Tests

Ejecuta:

```powershell
pytest -q
```

Documentación API (Swagger)

Con el servidor en marcha, visita:

- /api/schema/  -> OpenAPI JSON
- /api/schema/swagger-ui/  -> Swagger UI

CI

Se incluye un workflow de GitHub Actions (`.github/workflows/ci.yml`) que ejecuta los tests en pushes y PRs a `main`.

Despliegue (Render)

Para deploy en Render u otro PaaS, considera:
- Ejecutar `python manage.py collectstatic --noinput` durante el build
- Asegurar variables de entorno (SECRET_KEY, EMAIL_*, CELERY_BROKER_URL, etc.) en el entorno del servicio

Nota sobre despliegue automático (CI -> Render)

1. He añadido un workflow `./github/workflows/cd.yml` que se ejecuta en pushes a `main`. Para que funcione necesitas añadir en GitHub repo > Settings > Secrets las siguientes claves:

- `RENDER_SERVICE_ID` — el id del servicio en Render
- `RENDER_API_KEY` — tu API key de Render

2. El workflow instala dependencias, ejecuta `collectstatic` y `migrate` y luego llama a la API de Render para forzar un deploy. También incluí un `Procfile` con `web: gunicorn config.wsgi:application`.

3. Alternativa manual: en Render Dashboard configura Build Command y Start Command manualmente y haz deploy desde la UI.

SQLite on Render (Sprint-0 quick workaround)
-------------------------------------------
If you want to keep SQLite for now (note: Render's filesystem is ephemeral), do the following to avoid the "unable to open database file" error during build:

1) Build Command (Render service settings)

   ```bash
   pip install -r requirements.txt && touch db.sqlite3 && chmod 666 db.sqlite3 && python manage.py collectstatic --noinput && python manage.py migrate --noinput
   ```

   This ensures a `db.sqlite3` file exists and is writable during the build/migrate step.

2) Start Command (Render service settings)

   Option A — use helper script (recommended):

   ```bash
   bash scripts/render_start.sh
   ```

   Option B — direct gunicorn (if you don't need the script):

   ```bash
   gunicorn -b 0.0.0.0:$PORT config.wsgi:application --workers 3
   ```

- Notes:
- The helper script `scripts/render_start.sh` is intentionally lightweight: it only ensures the SQLite file exists and then starts Gunicorn. It does NOT run `migrate` or `collectstatic`.
- For fastest startup on Render (free tier) run `migrate` and `collectstatic` during the Build step (recommended). Running them at Start makes the web process wait for those tasks and slows the first response.
- Remember: SQLite on Render is not persistent — data will be lost on redeploy. Switch to Postgres for production.

Notas sobre estáticos

- Usamos `static/` para los archivos de origen y `STATIC_ROOT` (por defecto `staticfiles/`) para el artefacto producido por `collectstatic` en deploy. Mantenerlas separadas evita mezclar fuentes y artefactos.

Qué falta / recomendaciones
- Revisar y consolidar `config/settings.py` para producción (secret management, allowed hosts, logging)
- Añadir más tests y documentación de arquitectura en `docs/`
- Verificar Redis local si planeas usar Celery (por defecto `redis://localhost:6379/0`)

Si querés, puedo:
- Añadir secciones más detalladas al README (deploy en Render, variables necesarias, comandos de mantenimiento)
- Crear el workflow CD para publicar en Render
