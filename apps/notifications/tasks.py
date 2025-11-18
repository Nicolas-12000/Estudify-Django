from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task

from apps.notifications.models import Notification
from apps.academics.models import Grade

User = get_user_model()


@shared_task
def send_welcome_email(user_id: int):
    """Send welcome email to a user and create a notification.

    This task is safe to call synchronously in tests (it runs immediately).
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

    # Create persistent notification
    Notification.objects.create(
        user=user,
        title='Bienvenido a Estudify',
        message='Tu cuenta ha sido creada correctamente. ¡Bienvenido!'
    )
    return True


@shared_task
def send_grade_notification_email(grade_id: int):
    """Notify student and create notification when a grade is created/updated."""
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

    # Avoid creating duplicate notifications for the same grade
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
    return True
