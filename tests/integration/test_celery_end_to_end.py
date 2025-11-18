import pytest
import time
from django.core import mail
from django.contrib.auth import get_user_model

from apps.notifications.tasks import send_welcome_email
from apps.notifications.models import Notification


@pytest.mark.django_db
def test_send_welcome_email_creates_notification_and_sends_mail():
    User = get_user_model()
    user = User.objects.create_user(username='e2e_user', email='e2e@example.com', password='p')

    # For local test runs (SQLite) avoid concurrent worker DB locks by running
    # Celery tasks eagerly. In CI integration job a real worker can be used.
    from django.conf import settings
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Trigger the task via .delay(); with eager=True it runs synchronously.
    send_welcome_email.delay(user.id)

    # wait/poll for notification to appear (worker real or eager)
    timeout = 5
    interval = 0.5
    waited = 0.0
    while waited < timeout:
        if Notification.objects.filter(user=user, title__icontains='Bienvenido').exists():
            break
        time.sleep(interval)
        waited += interval

    assert Notification.objects.filter(user=user, title__icontains='Bienvenido').exists()

    # If email backend is locmem, ensure email was sent
    assert len(mail.outbox) >= 1
