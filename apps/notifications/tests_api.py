from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

import pytest

from apps.notifications.models import Notification
from apps.notifications.views import NotificationListView, NotificationMarkReadView


User = get_user_model()


@pytest.mark.django_db
def test_list_notifications_returns_user_notifications():
    factory = APIRequestFactory()

    user1 = User.objects.create_user('u1', 'u1@example.com', 'pass')
    user2 = User.objects.create_user('u2', 'u2@example.com', 'pass')

    Notification.objects.create(user=user1, title='T1', message='M1')
    Notification.objects.create(user=user2, title='T2', message='M2')

    request = factory.get('/')
    force_authenticate(request, user=user1)
    view = NotificationListView.as_view()
    response = view(request)

    assert response.status_code == 200
    data = response.data
    # ListAPIView uses pagination -> response.data is a dict with 'results'
    results = data.get('results', []) if isinstance(data, dict) else data
    assert len(results) == 1
    assert results[0]['title'] == 'T1'


@pytest.mark.django_db
def test_mark_notification_read_by_owner_succeeds_and_by_other_forbidden():
    factory = APIRequestFactory()

    owner = User.objects.create_user('owner', 'owner@example.com', 'pass')
    other = User.objects.create_user('other', 'other@example.com', 'pass')

    notif = Notification.objects.create(user=owner, title='Hello', message='Msg')

    # Owner marks as read
    request = factory.patch('/')
    force_authenticate(request, user=owner)
    view = NotificationMarkReadView.as_view()
    response = view(request, pk=notif.pk)
    assert response.status_code == 200
    notif.refresh_from_db()
    assert notif.is_read is True

    # Another user cannot mark it
    notif2 = Notification.objects.create(user=owner, title='Hello2', message='Msg2')
    request2 = factory.patch('/')
    force_authenticate(request2, user=other)
    response2 = view(request2, pk=notif2.pk)
    assert response2.status_code == 403
