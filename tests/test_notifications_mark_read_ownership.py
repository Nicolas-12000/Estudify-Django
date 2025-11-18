import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification


@pytest.mark.django_db
def test_cannot_mark_other_users_notification_read():
    User = get_user_model()
    user_a = User.objects.create_user(username='a', email='a@example.com', password='p')
    user_b = User.objects.create_user(username='b', email='b@example.com', password='p')

    notif_b = Notification.objects.create(user=user_b, title='B1', message='m', is_read=False)

    client = APIClient()
    client.force_authenticate(user=user_a)

    resp = client.patch(f"/api/notifications/{notif_b.id}/mark_read/")
    assert resp.status_code == 403
    notif_b.refresh_from_db()
    assert notif_b.is_read is False


@pytest.mark.django_db
def test_owner_can_mark_notification_read():
    User = get_user_model()
    user = User.objects.create_user(username='owner', email='o@example.com', password='p')
    notif = Notification.objects.create(user=user, title='O1', message='m', is_read=False)

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.patch(f"/api/notifications/{notif.id}/mark_read/")
    assert resp.status_code == 200
    notif.refresh_from_db()
    assert notif.is_read is True
    assert notif.read_at is not None
