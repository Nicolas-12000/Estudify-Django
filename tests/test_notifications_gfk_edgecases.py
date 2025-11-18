import pytest
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.courses.models import Course


@pytest.mark.django_db
def test_notification_with_missing_related_object_is_listable():
    User = get_user_model()
    user = User.objects.create_user(username='u1', email='u1@example.com', password='p')

    # Choose ContentType of Course but use a non-existent object_id
    ct = ContentType.objects.get_for_model(Course)
    missing_id = 999999

    Notification.objects.create(
        user=user,
        title='Orphan',
        message='Related object is missing',
        content_type=ct,
        object_id=missing_id,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/notifications/')
    assert resp.status_code == 200
    data = resp.json()
    # Should include the notification even if related object doesn't exist
    assert any(n['title'] == 'Orphan' for n in data.get('results', data))
