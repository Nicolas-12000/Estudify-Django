from types import SimpleNamespace
import itertools

import pytest

from django.contrib.auth import get_user_model

from apps.api import permissions as perms
from apps.users.models import Profile


class DummyQuerySet:
    def __init__(self, result=True):
        self._result = result

    def exists(self):
        return self._result


class DummyEnrollments:
    def __init__(self, result=True):
        self._result = result

    def filter(self, **kwargs):
        return DummyQuerySet(self._result)


class DummyCourse:
    def __init__(self, enrollments_result=True):
        self.enrollments = DummyEnrollments(enrollments_result)


class DummyObj:
    def __init__(self, **attrs):
        for k, v in attrs.items():
            setattr(self, k, v)


def make_request(user, method="GET"):
    return SimpleNamespace(user=user, method=method)


_user_counter = itertools.count(1)


def make_user(**attrs):
    # Use simple object for permission checks (no DB needed)
    base = SimpleNamespace()
    base.is_authenticated = attrs.get("is_authenticated", True)
    base.is_staff = attrs.get("is_staff", False)
    base.is_admin_role = attrs.get("is_admin_role", False)
    base.is_teacher = attrs.get("is_teacher", False)
    base.is_student = attrs.get("is_student", False)
    # ensure unique id/username for equality checks
    base.id = attrs.get('id', next(_user_counter))
    base.username = attrs.get('username', f'user{base.id}')
    return base


def test_is_admin_user_allows_admin():
    user = make_user(is_admin_role=True, is_authenticated=True)
    req = make_request(user)
    assert perms.IsAdminUser().has_permission(req, None)


def test_is_teacher_or_admin_allows_teacher():
    user = make_user(is_teacher=True, is_authenticated=True)
    req = make_request(user)
    assert perms.IsTeacherOrAdmin().has_permission(req, None)


def test_grade_permission_student_can_get_but_not_post():
    student = make_user(is_student=True, is_authenticated=True)
    req_get = make_request(student, method="GET")
    req_post = make_request(student, method="POST")
    assert perms.GradePermission().has_permission(req_get, None)
    assert not perms.GradePermission().has_permission(req_post, None)


def test_course_permission_object_teacher_edit_own_course():
    teacher = make_user(is_teacher=True, is_authenticated=True)
    req_put = make_request(teacher, method="PUT")
    course_obj = DummyObj(teacher=teacher)
    assert perms.CoursePermission().has_object_permission(req_put, None, course_obj)


def test_subject_permission_student_enrolled_can_view():
    student = make_user(is_student=True, is_authenticated=True)
    req_get = make_request(student, method="GET")
    course = DummyCourse(enrollments_result=True)
    subject = DummyObj(course=course)
    assert perms.SubjectPermission().has_object_permission(req_get, None, subject)


@pytest.mark.django_db
def test_user_signal_creates_profile():
    User = get_user_model()
    user = User.objects.create_user(username="signal_user", email="s@example.com", password="pass123")
    # Signal should create profile
    assert Profile.objects.filter(user=user).exists()
