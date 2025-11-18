from types import SimpleNamespace

import pytest

from django.contrib.auth import get_user_model

from apps.core.management.commands import command_helpers as ch


@pytest.mark.django_db
def test_create_user_if_missing_applies_flags():
    # User model not directly used here
    stdout = SimpleNamespace(write=lambda s: None)
    stderr = SimpleNamespace(write=lambda s: None)
    style = SimpleNamespace(SUCCESS=lambda s: s)

    created, user = ch.create_user_if_missing(
        "helper_user",
        "h@example.com",
        "pass123",
        set_staff=True,
        set_superuser=False,
        role_attr="role",
        role_value=None,
        stdout=stdout,
        stderr=stderr,
        style=style,
    )

    assert created is True
    assert user is not None
    # staff flag applied
    assert user.is_staff is True


@pytest.mark.django_db
def test_apply_user_flags_sets_values():
    User = get_user_model()
    user = User.objects.create_user(username="u2", email="u2@example.com", password="p")
    ch._apply_user_flags(user, role_attr=None, role_value=None, set_staff=False, set_superuser=True)
    assert user.is_superuser is True
