from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        try:
            from apps.core.create_default_admin import create_default_admin
            create_default_admin()
        except Exception as e:
            print(f"⚠️ Error creating default admin: {e}")
