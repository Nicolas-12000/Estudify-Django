import itertools
from types import SimpleNamespace

from apps.api import permissions as api_permissions


# Simple counter to produce unique ids/usernames for test users so equality is unambiguous
_user_counter = itertools.count(1)


def make_user(**kwargs):
    # Create a lightweight user-like object with attributes used by permissions
    attrs = dict(is_authenticated=True, is_staff=False, is_admin_role=False, is_teacher=False, is_student=False)
    attrs.update(kwargs)
    # ensure unique id and username unless explicitly provided
    if 'id' not in attrs:
        attrs['id'] = next(_user_counter)
    if 'username' not in attrs:
        attrs['username'] = f"user{attrs['id']}"
    return SimpleNamespace(**attrs)


def make_request(user, method='GET'):
    return SimpleNamespace(user=user, method=method)


def test_is_admin_user_permission():
    perm = api_permissions.IsAdminUser()
    admin = make_user(is_staff=True)
    req = make_request(admin)
    assert perm.has_permission(req, None) is True

    anon = make_user(is_authenticated=False)
    req2 = make_request(anon)
    assert perm.has_permission(req2, None) is False


def test_is_teacher_or_admin_permission():
    perm = api_permissions.IsTeacherOrAdmin()
    teacher = make_user(is_teacher=True)
    assert perm.has_permission(make_request(teacher), None)

    admin = make_user(is_staff=True)
    assert perm.has_permission(make_request(admin), None)

    student = make_user(is_student=True)
    assert not perm.has_permission(make_request(student, method='POST'), None)


def test_is_owner_or_read_only():
    perm = api_permissions.IsOwnerOrReadOnly()
    user = make_user()
    other = make_user()
    # safe methods allowed
    req = make_request(user, method='GET')
    obj = SimpleNamespace(user=user)
    assert perm.has_object_permission(req, None, obj)

    # non-owner cannot write
    req2 = make_request(other, method='POST')
    assert not perm.has_object_permission(req2, None, obj)

    # owner can write
    req3 = make_request(user, method='PUT')
    assert perm.has_object_permission(req3, None, obj)


def test_grade_permission_student_vs_teacher():
    perm = api_permissions.GradePermission()
    teacher = make_user(is_teacher=True)
    student = make_user(is_student=True)

    # Teacher can POST
    assert perm.has_permission(make_request(teacher, method='POST'), None)

    # Student can GET but not POST
    assert perm.has_permission(make_request(student, method='GET'), None)
    assert not perm.has_permission(make_request(student, method='POST'), None)

    # object-level: student can view own grade
    grade_obj = SimpleNamespace(student=student)
    assert perm.has_object_permission(make_request(student, method='GET'), None, grade_obj)
    # student cannot modify
    assert not perm.has_object_permission(make_request(student, method='PUT'), None, grade_obj)


def test_course_permission_teacher_edit():
    perm = api_permissions.CoursePermission()
    teacher = make_user(is_teacher=True)
    other_teacher = make_user(is_teacher=True)
    course = SimpleNamespace(teacher=teacher, enrollments=SimpleNamespace(filter=lambda **k: []))

    # teacher can create/list
    assert perm.has_permission(make_request(teacher, method='POST'), None)

    # object-level: teacher can edit own course
    assert perm.has_object_permission(make_request(teacher, method='PUT'), None, course)

    # other teacher cannot edit
    assert not perm.has_object_permission(make_request(other_teacher, method='PUT'), None, course)
