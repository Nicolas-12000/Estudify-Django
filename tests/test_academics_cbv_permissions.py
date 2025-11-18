import pytest

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade


@pytest.mark.django_db
def test_student_cannot_view_other_students_grades():
    User = get_user_model()
    teacher = User.objects.create_user(username='g_t', email='t@example.com', password='p', role=User.UserRole.TEACHER)
    s1 = User.objects.create_user(username='g_s1', email='s1@example.com', password='p', role=User.UserRole.STUDENT)
    s2 = User.objects.create_user(username='g_s2', email='s2@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso G2', code='CG2', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Sub G2', code='SG2', course=course, teacher=teacher)

    CourseEnrollment.objects.create(student=s1, course=course, is_active=True)
    CourseEnrollment.objects.create(student=s2, course=course, is_active=True)

    Grade.objects.create(student=s1, subject=subject, value=4.0, graded_by=teacher)
    Grade.objects.create(student=s2, subject=subject, value=3.5, graded_by=teacher)

    client = APIClient()
    client.force_authenticate(user=s1)

    # s1 can get their own grade list
    resp = client.get('/api/grades/', {'student': s1.id})
    assert resp.status_code == 200
    data = resp.json()
    # normalize possible paginated response
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data

    # ensure s2's grade is not present
    for g in results or []:
        if isinstance(g, dict):
            assert g.get('student') == s1.id
        else:
            # entry may be an id string/number; fetch detail
            det = client.get(f"/api/grades/{g}/")
            assert det.status_code == 200
            assert det.json().get('student') == s1.id

    # attempt to get s2's detail should be forbidden or empty
    # fetch all grades and assert none belong to s2
    all_resp = client.get('/api/grades/')
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    if isinstance(all_data, dict) and 'results' in all_data:
        all_results = all_data['results']
    else:
        all_results = all_data

    for g in all_results or []:
        if isinstance(g, dict):
            assert g.get('student') != s2.id
        else:
            det = client.get(f"/api/grades/{g}/")
            assert det.status_code == 200
            assert det.json().get('student') != s2.id


@pytest.mark.django_db
def test_teacher_can_view_and_manage_grades_for_their_subjects():
    User = get_user_model()
    teacher = User.objects.create_user(username='g_tt', email='tt@example.com', password='p', role=User.UserRole.TEACHER)
    other_teacher = User.objects.create_user(username='g_ot', email='ot@example.com', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='g_ss', email='ss@example.com', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso G3', code='CG3', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Sub G3', code='SG3', course=course, teacher=teacher)

    CourseEnrollment.objects.create(student=student, course=course, is_active=True)

    Grade.objects.create(student=student, subject=subject, value=4.2, graded_by=teacher)

    client = APIClient()
    client.force_authenticate(user=teacher)

    # teacher can list grades for their subject
    resp = client.get('/api/grades/', {'subject_id': subject.id})
    assert resp.status_code == 200
    data = resp.json()
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data

    found = False
    for g in results or []:
        if isinstance(g, dict) and g.get('subject') == subject.id:
            found = True
            break
        if not isinstance(g, dict):
            det = client.get(f"/api/grades/{g}/")
            if det.status_code == 200 and det.json().get('subject') == subject.id:
                found = True
                break
    assert found

    # other_teacher should not see grades for this subject when filtering by subject
    client.force_authenticate(user=other_teacher)
    resp2 = client.get('/api/grades/', {'subject_id': subject.id})
    assert resp2.status_code == 200
    data2 = resp2.json()
    if isinstance(data2, dict) and 'results' in data2:
        results2 = data2['results']
    else:
        results2 = data2

    # since other_teacher is not teacher of the subject, they should not get the grade
    for g in results2 or []:
        if isinstance(g, dict):
            assert g.get('subject') != subject.id
        else:
            det = client.get(f"/api/grades/{g}/")
            assert det.status_code == 200
            assert det.json().get('subject') != subject.id
