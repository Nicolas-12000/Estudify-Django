from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario."""
    if created:
        from apps.users.models import Profile
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar/asegurar existencia del perfil tras guardar el usuario."""
    from apps.users.models import Profile
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    else:
        try:
            instance.profile.save()
        except Exception:
            # defensivo: si algo falla, no bloquear el flujo de creación de usuario
            pass


@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    """Enviar email de bienvenida de forma asíncrona cuando se crea el usuario.

    Este handler intenta usar Celery task `send_welcome_email` si está disponible.
    """
    if created:
        try:
            # importar aquí para evitar importaciones circulares si Celery no está configurado
            from apps.notifications.tasks import send_welcome_email
            # enviar tarea asíncrona (si Celery configurado)
            send_welcome_email.delay(instance.id)
        except Exception:
            # si no está Celery o falla, ignoramos (no queremos romper creación de usuario)
            pass
