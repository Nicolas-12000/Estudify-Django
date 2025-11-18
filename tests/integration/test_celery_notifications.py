import time
import pytest
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.notifications.models import Notification
from apps.notifications.tasks import send_welcome_email

# Start a test Celery worker so tasks are processed with the same app/settings
from celery.contrib.testing.worker import start_worker
from config.celery import app as celery_app
from kombu import Connection as KombuConnection


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_send_welcome_email_creates_notification(db, settings):
    """Integration test: enqueue the Celery task and wait for the Notification.

    Uses polling with a configurable timeout to avoid flakes.
    Requires Redis + Celery worker (CI integration job provides them).
    """
    # Ensure emails don't fail the test environment
    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    User = get_user_model()
    user = User.objects.create_user(username="celery_user", email="celery@example.com", password="pass")
    # Make sure the new user is committed so the external Celery worker can see it
    transaction.commit()

    # If the configured broker isn't reachable (e.g. no Redis in this
    # environment), skip the test instead of failing the entire suite.
    try:
        with KombuConnection(celery_app.conf.broker_url) as _conn:
            # force an immediate connection attempt
            _conn.ensure_connection(max_retries=0)
    except Exception:
        pytest.skip(f"Broker {celery_app.conf.broker_url!r} not available. Skipping integration test")

    # Start a test worker that shares the same Celery app and settings so
    # the worker can see the test database (we use transaction=True and
    # commit above). Using `start_worker` keeps the worker lifecycle scoped
    # to the test and avoids needing a separate external worker process.
    with start_worker(celery_app, pool='solo', perform_ping_check=False):
        # Enqueue the task
        send_welcome_email.delay(user.id)

        # Poll DB until the notification appears or timeout
        timeout = getattr(settings, 'INTEGRATION_TASK_TIMEOUT', 20)
        interval = 0.5
        deadline = time.time() + timeout
        found = False
        while time.time() < deadline:
            if Notification.objects.filter(user=user, title__icontains="Bienvenido").exists():
                found = True
                break
            time.sleep(interval)
    assert found, "Notification was not created by Celery worker within timeout"
