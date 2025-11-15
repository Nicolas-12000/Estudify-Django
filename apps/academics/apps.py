from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.academics'

    def ready(self):
        # Importar signals para registrarlos cuando la app esté lista
        try:
            import apps.academics.signals  # noqa: F401
        except Exception:
            pass
