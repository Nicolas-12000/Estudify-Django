from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.academics.models import Grade


@receiver(post_save, sender=Grade)
def notify_student_on_grade_creation(sender, instance, created, **kwargs):
    """Notificar al estudiante cuando se crea una calificación (asíncrono si hay Celery)."""
    if created:
        try:
            from apps.notifications.tasks import send_grade_notification_email
            send_grade_notification_email.delay(instance.id)
        except Exception:
            # Si no hay Celery o falla, continuar sin interrumpir
            pass


@receiver(post_save, sender=Grade)
def log_grade_change(sender, instance, created, **kwargs):
    """Registrar en logs la creación/actualización de calificaciones."""
    import logging
    logger = logging.getLogger(__name__)
    action = 'creada' if created else 'actualizada'
    try:
        graded_by = instance.graded_by.username if instance.graded_by else 'sistema'
        logger.info(
            f'Calificación {action}: {instance.student.username} - '
            f'{instance.subject.name}: {instance.value} por {graded_by}'
        )
    except Exception:
        # No morir por un fallo en logging de una señal
        logger.exception('Error al loggear cambio de calificación')
