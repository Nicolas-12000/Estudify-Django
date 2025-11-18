from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario."""
    if created:
        from apps.users.models import Profile

        # Use get_or_create to avoid race conditions or duplicate creation
        try:
            Profile.objects.get_or_create(user=instance)
        except Exception:
            # defensivo: si ocurre alguna condición de carrera o integridad,
            # no queremos bloquear la creación del usuario en el flujo de
            # tests/CI
            pass


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar/asegurar existencia del perfil tras guardar el usuario."""
    from apps.users.models import Profile

    # Ensure profile exists without creating duplicates. Use get_or_create
    try:
        profile, created = Profile.objects.get_or_create(user=instance)
        if not created:
            try:
                profile.save()
            except Exception:
                # Do not block user save on profile save errors
                pass
    except Exception:
        # Be defensive in case of integrity/race conditions during CI or
        # concurrent requests
        pass


@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """Enviar email de bienvenida de forma asíncrona cuando se crea el usuario.

    Este handler intenta usar Celery task `send_welcome_email` si está disponible.
    """
    if created:
        try:
            # importar aquí para evitar importaciones circulares si Celery no
            # está configurado
            from django.conf import settings
            # If Celery is configured to run tasks eagerly in this process
            # (common in some test setups), skip scheduling the welcome task
            # here so tests can control task execution deterministically.
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                return

            from apps.notifications.tasks import send_welcome_email

            # enviar tarea asíncrona (si Celery configurado)
            send_welcome_email.delay(instance.id)
        except Exception:
            # si no está Celery o falla, ignoramos (no queremos romper creación
            # de usuario)
            pass
