from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
from django.db import OperationalError, transaction
from celery.utils.log import get_task_logger

from apps.notifications.models import Notification
from apps.academics.models import Grade

logger = get_task_logger(__name__)
User = get_user_model()


# Retry on OperationalError (e.g., SQLite locked) with exponential backoff
@shared_task(bind=True, autoretry_for=(OperationalError,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def send_welcome_email(self, user_id: int):
    """Send welcome email to a user and create a notification.

    Uses automatic retries on database OperationalError to handle transient
    'database is locked' situations (SQLite). In production use Postgres
    which avoids these issues when running concurrent workers.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False

    subject = 'Bienvenido a Estudify'
    context = {'user': user}
    message = render_to_string('emails/welcome.txt', context)
    html_message = render_to_string('emails/welcome.html', context)

    # Use Django send_mail (backend controlled in settings)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)

    # Create persistent notification inside a transaction; retry on OperationalError
    try:
        with transaction.atomic():
            Notification.objects.create(
                user=user,
                title='Bienvenido a Estudify',
                message='Tu cuenta ha sido creada correctamente. ¡Bienvenido!'
            )
    except OperationalError:
        logger.exception('OperationalError when creating welcome notification, will retry')
        raise

    return True


@shared_task(bind=True, autoretry_for=(OperationalError,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def send_grade_notification_email(self, grade_id: int):
    """Notify student and create notification when a grade is created/updated.

    Protects against transient SQLite locking errors by retrying. Prefer Postgres
    in CI/production when running Celery workers concurrently.
    """
    try:
        grade = Grade.objects.select_related('student', 'graded_by', 'subject').get(id=grade_id)
    except Grade.DoesNotExist:
        return False

    student = grade.student
    subject = f'Nueva calificación en {grade.subject.name}'
    context = {'student': student, 'grade': grade}
    message = render_to_string('emails/grade_notification.txt', context)
    html_message = render_to_string('emails/grade_notification.html', context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student.email], html_message=html_message)

    # Create notification safely with transaction and avoid duplicates
    try:
        with transaction.atomic():
            exists = Notification.objects.filter(
                user=student,
                notification_type='grade',
                object_id=grade.id,
            ).exists()

            if not exists:
                Notification.objects.create(
                    user=student,
                    title=subject,
                    message=f'Tu calificación en {grade.subject.name} es {grade.value}',
                    content_type=None,
                    object_id=grade.id,
                    notification_type='grade',
                )
    except OperationalError:
        logger.exception('OperationalError when creating grade notification, will retry')
        raise

    return True
