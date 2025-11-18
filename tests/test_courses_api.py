import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from apps.courses.models import Course, CourseEnrollment


@pytest.mark.django_db
def test_course_list_as_admin_returns_all():
    User = get_user_model()
    admin = User.objects.create_user(
        username='admin',
        email='a@example.com',
        password='p',
        role=User.UserRole.ADMIN,
        is_staff=True,
    )

    Course.objects.create(name='Curso 1', code='C1', academic_year=2025, semester=1)
    Course.objects.create(name='Curso 2', code='C2', academic_year=2025, semester=1)

    client = APIClient()
    client.force_authenticate(user=admin)

    resp = client.get('/api/courses/')
    assert resp.status_code == 200
    data = resp.json()
    results = data.get('results') or data
    assert len(results) == 2


@pytest.mark.django_db
def test_course_list_as_student_shows_only_enrolled():
    User = get_user_model()
    student = User.objects.create_user(
        username='stud2',
        email='s2@example.com',
        password='p',
        role=User.UserRole.STUDENT,
    )

    c1 = Course.objects.create(
        name='Curso A', code='CA', academic_year=2025, semester=1
    )
    Course.objects.create(
        name='Curso B', code='CB', academic_year=2025, semester=1
    )

    CourseEnrollment.objects.create(student=student, course=c1)

    client = APIClient()
    client.force_authenticate(user=student)

    resp = client.get('/api/courses/')
    assert resp.status_code == 200
    data = resp.json()
    results = data.get('results') or data
    # student should only see 1 course
    assert len(results) == 1
    assert results[0]['id'] == c1.id


@pytest.mark.django_db
def test_student_cannot_retrieve_unenrolled_course():
    User = get_user_model()
    student = User.objects.create_user(
        username='stud3',
        email='s3@example.com',
        password='p',
        role=User.UserRole.STUDENT,
    )

    c = Course.objects.create(name='Curso X', code='CX', academic_year=2025, semester=1)

    client = APIClient()
    client.force_authenticate(user=student)

    resp = client.get(f'/api/courses/{c.id}/')
    # should be 404 because get_queryset filters out unenrolled courses for students
    assert resp.status_code == 404


@pytest.mark.django_db
def test_course_detail_includes_classroom_and_schedule_for_admin():
    User = get_user_model()
    admin = User.objects.create_user(
        username='admin2',
        email='a2@example.com',
        password='p',
        role=User.UserRole.ADMIN,
        is_staff=True,
    )

    c = Course.objects.create(name='Curso Det', code='CD1', academic_year=2025, semester=1)
    # create a timeslot, classroom and session to expose via API
    from apps.courses.models import TimeSlot, Classroom, CourseSession
    ts = TimeSlot.objects.create(
        day_of_week=0, start_time='08:00', end_time='10:00'
    )
    room = Classroom.objects.create(name='Aula 101')
    CourseSession.objects.create(course=c, timeslot=ts, classroom_fk=room)
    client = APIClient()
    client.force_authenticate(user=admin)

    resp = client.get(f'/api/courses/{c.id}/')
    assert resp.status_code == 200
    data = resp.json()
    # sessions should be present and include timeslot and classroom info
    sessions = data.get('sessions')
    assert sessions and len(sessions) == 1
    sess = sessions[0]
    assert sess['classroom']['name'] == 'Aula 101'
    assert sess['timeslot']['start_time'] == '08:00:00'
