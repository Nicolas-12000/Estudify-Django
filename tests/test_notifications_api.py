import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_mark_all_read_endpoint(api_client):
    User = get_user_model()
    user = User.objects.create_user(username='notif_user', email='n@example.com', password='p')

    # create two unread and one already read
    Notification.objects.create(user=user, title='A', message='a', is_read=False)
    Notification.objects.create(user=user, title='B', message='b', is_read=False)
    Notification.objects.create(user=user, title='C', message='c', is_read=True)

    api_client.force_authenticate(user=user)

    resp = api_client.post('/api/notifications/mark_all_read/')
    assert resp.status_code == 200
    assert 'updated' in resp.data
    assert resp.data['updated'] == 2

    # ensure all notifications are marked read
    assert Notification.objects.filter(user=user, is_read=False).count() == 0
