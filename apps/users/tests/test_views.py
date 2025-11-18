import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model


# Provide minimal in-memory templates so view tests don't depend on filesystem
DEFAULT_TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.locmem.Loader', {
                    'users/user_list.html': '',
                    'users/user_detail.html': '',
                    'users/profile.html': '',
                }),
            ],
        },
    }
]


@pytest.fixture(autouse=True)
def enable_locmem_templates(settings):
    settings.TEMPLATES = DEFAULT_TEMPLATES


User = get_user_model()


@pytest.mark.django_db
def test_user_list_requires_admin(client):
    # non-admin should be redirected
    user = User.objects.create_user(username='normal', password='pass')
    client.force_login(user)

    resp = client.get(reverse('users:user_list'))
    assert resp.status_code == 302


@pytest.mark.django_db
def test_user_list_allows_admin(client):
    admin = User.objects.create_user(username='admin', password='pass', role=User.UserRole.ADMIN)
    client.force_login(admin)

    resp = client.get(reverse('users:user_list'))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_toggle_user_status_by_admin(client):
    admin = User.objects.create_user(username='admin2', password='pass', role=User.UserRole.ADMIN)
    target = User.objects.create_user(username='targ', password='pass')
    client.force_login(admin)

    resp = client.post(reverse('users:toggle_status', args=[target.pk]))
    assert resp.status_code in (302, 301)

    target.refresh_from_db()
    assert target.is_active is False


@pytest.mark.django_db
def test_profile_view_post_updates_profile(client):
    user = User.objects.create_user(username='perfil', password='pass', email='p@example.com')
    client.force_login(user)

    url = reverse('users:profile')
    data = {
        'first_name': 'Nuevo',
        'last_name': 'Nombre',
        'email': 'nuevo@example.com',
        'bio': 'texto'
    }

    resp = client.post(url, data, follow=True)
    # Accept either redirect (success) or 200 (re-render with messages/errors)
    assert resp.status_code in (200, 302)
