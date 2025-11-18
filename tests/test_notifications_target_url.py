import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification


@pytest.mark.django_db
def test_notifications_list_includes_target_url():
    User = get_user_model()
    user = User.objects.create_user(username="tuser", email="t@example.com", password="p")

    Notification.objects.create(
        user=user,
        title="Has un nuevo curso",
        message="Se ha creado un nuevo curso",
        is_read=False,
        target_url="/courses/123/",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/notifications/")
    assert resp.status_code == 200
    results = resp.data.get("results") or resp.data
    # If paginated, results is a list under 'results'
    first = results[0] if isinstance(results, list) else results["results"][0]
    assert first.get("target_url") == "/courses/123/"
