import os

import pytest

from apps.core.management.commands import command_helpers


def test_env_or_default(monkeypatch):
    monkeypatch.setenv('SOME_KEY', 'value')
    assert command_helpers.env_or_default('SOME_KEY', 'x') == 'value'
    assert command_helpers.env_or_default('MISSING', 'd') == 'd'


def test_normalize_user_tuples():
    data = (("u1", "First", "Last"),)
    out = command_helpers.normalize_user_tuples(data)
    assert isinstance(out, list)
    assert out[0][0] == 'u1'


class DummyUser:
    class UserRole:
        TEACHER = 'teacher'
        STUDENT = 'student'
        ADMIN = 'admin'

    def __init__(self):
        self.role = None
        self.is_staff = False
        self.is_superuser = False
        self.custom_flag = False


def test_apply_user_flags_maps_is_flags_to_role_and_sets_staff_superuser():
    user = DummyUser()
    # map is_teacher -> role
    command_helpers._apply_user_flags(user, 'is_teacher', None, set_staff=True, set_superuser=True)
    assert user.role == DummyUser.UserRole.TEACHER
    assert user.is_staff is True
    assert user.is_superuser is True


def test_apply_user_flags_sets_attribute_when_available():
    user = DummyUser()
    command_helpers._apply_user_flags(user, 'custom_flag', True, set_staff=False, set_superuser=False)
    assert user.custom_flag is True


def test_apply_user_flags_no_role_and_no_attr_does_nothing():
    user = DummyUser()
    # unknown attribute; should not raise
    command_helpers._apply_user_flags(user, 'nonexistent_attr', None, set_staff=False, set_superuser=False)
    assert getattr(user, 'nonexistent_attr', None) is None
