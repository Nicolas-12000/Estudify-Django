import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.notifications.models import Notification


@pytest.mark.django_db
def test_mark_all_read_only_affects_authenticated_user():
    User = get_user_model()
    user_a = User.objects.create_user(
        username="user_a", email="a@example.com", password="p"
    )
    user_b = User.objects.create_user(
        username="user_b", email="b@example.com", password="p"
    )

    Notification.objects.create(user=user_a, title="A1", message="m", is_read=False)
    Notification.objects.create(user=user_a, title="A2", message="m", is_read=False)
    Notification.objects.create(user=user_b, title="B1", message="m", is_read=False)

    client = APIClient()
    client.force_authenticate(user=user_a)

    resp = client.post("/api/notifications/mark_all_read/")

    assert resp.status_code == 200
    assert resp.data.get("updated") == 2
    assert (
        Notification.objects.filter(user=user_a, is_read=False).count() == 0
    )
    assert Notification.objects.filter(user=user_b, is_read=False).count() == 1
