import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from apps.courses.models import Course, CourseEnrollment


@pytest.mark.django_db
def test_student_can_view_own_attendance_but_cannot_create():
    User = get_user_model()
    teacher = User.objects.create_user(username='att_t', email='t@example.com', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='att_s', email='s@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso A', code='CA1', academic_year=2025, semester=1, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course, is_active=True)

    # Create attendance record via ORM
    from apps.academics.models import Attendance
    att = Attendance.objects.create(student=student, course=course, date='2025-01-10', status='PRESENT', recorded_by=teacher)

    client = APIClient()
    client.force_authenticate(user=student)

    # Student can view their attendance
    resp = client.get(f'/api/attendance/{att.id}/')
    assert resp.status_code == 200

    # Student cannot create attendance records
    payload = {'student': student.id, 'course': course.id, 'date': '2025-01-11', 'status': 'PRESENT'}
    resp2 = client.post('/api/attendance/', payload, format='json')
    assert resp2.status_code in (403, 401)


@pytest.mark.django_db
def test_teacher_can_create_and_list_attendance():
    User = get_user_model()
    teacher = User.objects.create_user(username='att_tt', email='tt@example.com', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='att_ss', email='ss@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso B', code='CB1', academic_year=2025, semester=1, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course, is_active=True)

    client = APIClient()
    client.force_authenticate(user=teacher)

    payload = {'student': student.id, 'course': course.id, 'date': '2025-02-01', 'status': 'PRESENT'}
    resp = client.post('/api/attendance/', payload, format='json')
    assert resp.status_code == 201
    data = resp.json()
    assert data.get('recorded_by') == teacher.id

    # Teacher can list attendances for their course
    resp2 = client.get('/api/attendance/', {'course': course.id})
    assert resp2.status_code == 200
    items = resp2.json()
    # Handle paginated responses (DRF PageNumberPagination) and plain lists
    if isinstance(items, dict) and 'results' in items:
        results = items['results']
    else:
        results = items

    # Normalize: results may contain dict entries or primitive ids
    found = False
    for it in results or []:
        if isinstance(it, dict) and it.get('id') == data.get('id'):
            found = True
            break
        # allow if API returns a list of ids
        if not isinstance(it, dict) and str(it) == str(data.get('id')):
            found = True
            break

    assert found, 'Created attendance record not found in attendance list response'
