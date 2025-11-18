import pytest
from django.contrib.auth import get_user_model

from apps.users.forms import UserRegistrationForm, UserProfileForm


User = get_user_model()


@pytest.mark.django_db
def test_user_registration_email_unique():
    # given
    User.objects.create_user(username='existing', email='exist@example.com', password='pass')

    data = {
        'username': 'newuser',
        'email': 'exist@example.com',
        'first_name': 'New',
        'last_name': 'User',
        'role': User.UserRole.STUDENT,
        'password1': 'ComplexPass123!',
        'password2': 'ComplexPass123!',
    }

    form = UserRegistrationForm(data=data)

    # when
    valid = form.is_valid()

    # then
    assert not valid
    assert 'email' in form.errors
    assert any('registrado' in e for e in form.errors['email'])


@pytest.mark.django_db
def test_userprofileform_save_updates_user_and_profile():
    # create user and profile
    user = User.objects.create_user(username='u1', email='u1@example.com', password='pass')
    profile = user.profile

    data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': 'updated@example.com',
        'phone': '123456789',
        'date_of_birth': '1990-01-01',
        'bio': 'bio text',
        'address': 'Calle 1',
        'city': 'Ciudad',
        'country': 'Pais'
    }

    form = UserProfileForm(data=data, instance=profile)
    assert form.is_valid(), form.errors
    form.save()

    user.refresh_from_db()
    profile.refresh_from_db()

    assert user.first_name == 'Updated'
    assert user.email == 'updated@example.com'
    assert profile.bio == 'bio text'
