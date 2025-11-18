import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from apps.courses.models import Course, CourseEnrollment, Subject
from apps.academics.models import Grade


@pytest.mark.django_db
def test_course_students_action_returns_enrolled_students():
    User = get_user_model()
    teacher = User.objects.create_user(username='tcs', email='tcs@example.com', password='p', role=User.UserRole.TEACHER)
    s1 = User.objects.create_user(username='s1', email='s1@example.com', password='p', role=User.UserRole.STUDENT)
    s2 = User.objects.create_user(username='s2', email='s2@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso Students', code='CS1', academic_year=2025, semester=1, teacher=teacher)
    CourseEnrollment.objects.create(student=s1, course=course)

    client = APIClient()
    client.force_authenticate(user=teacher)

    resp = client.get(f'/api/courses/{course.id}/students/')
    assert resp.status_code == 200
    data = resp.json()
    # should return list with only s1
    assert any(d['id'] == s1.id for d in data)
    assert not any(d['id'] == s2.id for d in data)


@pytest.mark.django_db
def test_grade_create_sets_graded_by_and_student_cannot_create():
    User = get_user_model()
    teacher = User.objects.create_user(username='tg', email='tg@example.com', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='sg', email='sg@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso G', code='CG1', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Sub G', code='SG1', course=course, teacher=teacher)

    CourseEnrollment.objects.create(student=student, course=course)

    client = APIClient()
    client.force_authenticate(user=teacher)

    payload = {'student': student.id, 'subject': subject.id, 'value': '4.0', 'weight': '100.00'}
    resp = client.post('/api/grades/', payload, format='json')
    assert resp.status_code == 201
    data = resp.json()
    # graded_by should be the teacher id
    assert data.get('graded_by') == teacher.id

    # Now ensure student cannot create a grade
    client.force_authenticate(user=student)
    resp2 = client.post('/api/grades/', payload, format='json')
    assert resp2.status_code in (403, 400)


@pytest.mark.django_db
def test_grade_statistics_action_returns_expected_structure():
    User = get_user_model()
    teacher = User.objects.create_user(username='tstat', email='tstat@example.com', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='sstat', email='sstat@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso Stat', code='CSTAT', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Sub Stat', code='SSTAT', course=course, teacher=teacher)

    Grade.objects.create(student=student, subject=subject, value=4.5, graded_by=teacher)
    Grade.objects.create(student=student, subject=subject, value=3.0, graded_by=teacher)

    client = APIClient()
    client.force_authenticate(user=teacher)

    resp = client.get('/api/grades/statistics/', {'subject_id': subject.id})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # each item should include the normalized keys
    assert all('subject_name' in item for item in data)
