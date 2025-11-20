from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario."""
    if created:
        from apps.users.models import Profile
        # Crea solo si no existe (¡muy importante!)
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar o actualizar perfil siempre después de guardar usuario."""
    from apps.users.models import Profile
    profile, created = Profile.objects.get_or_create(user=instance)
    try:
        profile.save()
    except Exception:
        pass

@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """Envía email de bienvenida usando Celery (si lo usas)."""
    if created:
        try:
            from django.conf import settings
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                return
            from apps.notifications.tasks import send_welcome_email
            send_welcome_email.delay(instance.id)
            send_welcome_email.delay(instance.id)
        except Exception:
            pass
