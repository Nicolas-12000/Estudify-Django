# Estudify

![codecov](https://codecov.io/gh/Nicolas-12000/Estudify-Django/branch/main/graph/badge.svg)

> Plataforma de gestión académica

Este repositorio contiene el código fuente de `Estudify`, una plataforma de gestión académica desarrollada con Django. El proyecto sigue buenas prácticas de ingeniería: principios de diseño (SOLID, KISS), desarrollo guiado por pruebas (TDD), convenciones de estilo PEP8, y la arquitectura MVT. Aquí encontrarás la implementación, tests automatizados, documentación y la configuración de CI para ejecutar y reportar pruebas.

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
# 🎓 ESTUDIFY - Sistema de Gestión Académica

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![DRF](https://img.shields.io/badge/DRF-3.15-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

Sistema completo de gestión académica desarrollado con Django. El proyecto está en fase avanzada de desarrollo: la mayor parte de las funcionalidades core están implementadas y la suite de tests está en ejecución.

## 📋 Características Principales

### Funcionalidades Core
- **Autenticación y Autorización**: Sistema de roles (Admin, Docente, Estudiante)
- **Gestión de Cursos**: CRUD de cursos y materias
- **Calificaciones**: Registro y consulta de notas con varios tipos de evaluación
- **Asistencia**: Control de asistencia con estados (Presente, Ausente, Tarde, Excusado)
- **Dashboard**: Estadísticas y métricas
- **Reportes**: Generación de boletines y reportes en PDF/Excel
- **Notificaciones**: Tareas asíncronas con Celery (pendiente: plantillas y señales)
- **API REST**: API documentada con Swagger/OpenAPI

### Características Técnicas
- **Testing**: Tests con `pytest` y `pytest-django`; se generan reportes de cobertura con `coverage.py` (consulta `coverage.xml`).
- **CI/CD**: GitHub Actions ejecuta tests, genera artefactos (junit/coverage) y realiza verificaciones automáticas.
- **Gráficos**: Visualizaciones con Chart.js
- **UI/UX**: Diseño responsive con Bootstrap 5
- **Seguridad**: Validaciones en modelos y permisos en la API

## 🏗️ Arquitectura

```
ESTUDIFY/
├── apps/
│   ├── core/           # Modelos base y utilidades comunes
│   ├── users/          # Autenticación y perfiles
│   ├── courses/        # Gestión de cursos y materias
│   ├── academics/      # Calificaciones y asistencia
│   ├── reports/        # Dashboard y reportes
│   ├── notifications/  # Sistema de notificaciones
│   └── api/            # API REST con DRF
├── config/             # Configuración Django y Celery
├── templates/          # Plantillas HTML
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── tests/              # Tests unitarios e integración
├── docs/               # Documentación adicional
├── media/              # Archivos subidos por usuarios
└── utils/              # Funciones de utilidad
```

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.11+
- Redis (para Celery)
- Git

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/estudify.git
cd estudify
```

### 2. Crear Entorno Virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env
# Editar .env con tu configuración
```

**Variables importantes:**
```env
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (opcional, para notificaciones)
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# Celery (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 5. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7. Cargar Datos de Prueba (Opcional)
```bash
python manage.py loaddata fixtures/initial_data.json
```

### 8. Ejecutar el Servidor
```bash
python manage.py runserver
```

Accede a: http://localhost:8000

### 9. Ejecutar Celery Worker (Terminal separada)
```bash
# Asegúrate de tener Redis corriendo
celery -A config worker -l info
```

## 🧪 Testing

### Ejecutar Todos los Tests
```bash
pytest
```

### Tests con Cobertura
```bash
pytest --cov=apps --cov-report=html
```

## 📊 Modelos de Datos

### User (Usuario)
```python
- username: CharField (único)
- email: EmailField
- role: CharField (ADMIN, TEACHER, STUDENT)
- first_name, last_name: CharField
- phone: CharField
- avatar: ImageField
- date_of_birth: DateField
```

### Course (Curso)
```python
- name: CharField
- code: CharField (único por periodo)
- academic_year: IntegerField
- semester: IntegerField
- teacher: ForeignKey(User)
- max_students: PositiveIntegerField
```

### Subject (Materia)
```python
- name: CharField
- code: CharField (único)
- credits: PositiveIntegerField
- course: ForeignKey(Course)
- teacher: ForeignKey(User)
```

### Grade (Calificación)
```python
- student: ForeignKey(User)
- subject: ForeignKey(Subject)
- value: DecimalField (0.0 - 5.0)
- grade_type: CharField (QUIZ, EXAM, etc.)
- weight: DecimalField
- graded_by: ForeignKey(User)
```

### Attendance (Asistencia)
```python
- student: ForeignKey(User)
- course: ForeignKey(Course)
- date: DateField
- status: CharField (PRESENT, ABSENT, LATE, EXCUSED)
- recorded_by: ForeignKey(User)
```

## 🔌 API REST

### Autenticación
La API requiere autenticación. Usa SessionAuthentication o BasicAuthentication.

### Endpoints Principales

**Usuarios**
```
GET    /api/users/              # Listar usuarios
POST   /api/users/              # Crear usuario
GET    /api/users/{id}/         # Detalle
GET    /api/users/me/           # Usuario actual
POST   /api/users/{id}/toggle_status/  # Activar/desactivar
```

**Cursos**
```
GET    /api/courses/            # Listar cursos
POST   /api/courses/            # Crear curso
GET    /api/courses/{id}/       # Detalle
GET    /api/courses/{id}/students/  # Estudiantes inscritos
GET    /api/courses/{id}/subjects/  # Materias del curso
```

**Calificaciones**
```
GET    /api/grades/             # Listar calificaciones
POST   /api/grades/             # Crear calificación
GET    /api/grades/statistics/  # Estadísticas
```

**Asistencia**
```
GET    /api/attendance/         # Listar asistencias
POST   /api/attendance/         # Registrar asistencia
GET    /api/attendance/statistics/  # Estadísticas
```

### Documentación Interactiva
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 📈 Dashboard y Reportes

### Gráficos Disponibles
1. **Rendimiento Académico**: Promedio por materia (Bar Chart)
2. **Asistencia Mensual**: Tendencia de asistencia (Line Chart)
3. **Distribución de Calificaciones**: Por tipo de evaluación (Pie Chart)

### Exportación de ReportES
- **PDF**: Boletines individuales con ReportLab
- **Excel**: Reportes consolidados con pandas/openpyxl

## 🔔 Sistema de Notificaciones

### Tareas Asíncronas con Celery
- Notificación de nuevas calificaciones
- Recordatorios de registro de asistencia
- Emails de bienvenida
- Confirmación de inscripción en cursos

### Configuración de Email
Para producción, configura SMTP en `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

## 🚢 Despliegue en Render

### 1. Preparación
```bash
# Crear archivo build.sh
#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

### 2. Configuración en Render
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn config.wsgi:application`
- **Environment**: Python 3.11

### 3. Variables de Entorno
Configura en el dashboard de Render:
```
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com
DATABASE_URL=postgresql://...
CELERY_BROKER_URL=redis://...
```

### 4. Workers Adicionales
Para Celery, crea un servicio adicional:
- **Start Command**: `celery -A config worker -l info`

## 🛠️ Desarrollo

### Estructura de Commits
```
feat: Nueva funcionalidad
fix: Corrección de bug
docs: Cambios en documentación
test: Agregar o modificar tests
refactor: Refactorización de código
style: Cambios de formato
```

### Branching Strategy
- `main`: Producción
- `develop`: Desarrollo
- `feature/*`: Nuevas funcionalidades
- `fix/*`: Correcciones

### Pre-commit Hooks (Recomendado)
```bash
pip install pre-commit
pre-commit install
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'feat: Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request


## 👥 Autores

- **Nicolás García** - *Desarrollo inicial* - [Nicolas-12000](https://github.com/Nicolas-12000)

## 🙏 Agradecimientos

- Django Documentation
- DRF Documentation
- Bootstrap Team
- Chart.js Team

## 📞 Soporte

Para soporte y preguntas:
- 📧 Email: soporte@estudify.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/estudify/issues)
- 📖 Docs: [Documentación](https://docs.estudify.com)

---

**Hecho con ❤️ y ☕ por el equipo de Estudify**
