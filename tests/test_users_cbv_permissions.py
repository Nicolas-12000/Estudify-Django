import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_users_me_endpoint_returns_current_user():
    User = get_user_model()
    user = User.objects.create_user(username='u_me', email='u_me@example.com', password='p', role=User.UserRole.STUDENT)

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/users/me/')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('id') == user.id
    assert data.get('email') == user.email


@pytest.mark.django_db
def test_only_admin_can_create_users():
    User = get_user_model()

    teacher = User.objects.create_user(username='t_nonadmin', email='t@example.com', password='p', role=User.UserRole.TEACHER)
    client = APIClient()
    client.force_authenticate(user=teacher)

    payload = {'username': 'newuser', 'email': 'new@example.com', 'password': 'p', 'role': User.UserRole.STUDENT}
    resp = client.post('/api/users/', payload, format='json')
    assert resp.status_code in (403, 401)

    # Now create an admin user and ensure creation is allowed
    admin = User.objects.create_user(username='admin1', email='admin@example.com', password='p', role=User.UserRole.ADMIN)
    client.force_authenticate(user=admin)
    resp2 = client.post('/api/users/', payload, format='json')
    assert resp2.status_code == 201
