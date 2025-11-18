from types import SimpleNamespace

import pytest

from django.contrib.auth import get_user_model

from apps.notifications import tasks


@pytest.mark.django_db
def test_send_welcome_email_eager(monkeypatch, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    User = get_user_model()
    user = User.objects.create_user(username="wuser", email="w@example.com", password="pw")

    # Patch Notification.objects.create to avoid requiring Notification model implementation
    fake_created = {}

    class _FakeMgr:
        def create(self, **kwargs):
            fake_created.update(kwargs)

    monkeypatch.setattr(tasks, 'Notification', SimpleNamespace(objects=_FakeMgr()))

    # Ensure send_mail uses console backend or patch send_mail to capture calls
    monkeypatch.setattr('django.core.mail.send_mail', lambda *a, **k: 1)

    result = tasks.send_welcome_email(user.id)
    assert result is True
    # Check that our fake Notification was populated
    assert fake_created.get('user') == user
