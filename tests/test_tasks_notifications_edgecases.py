import pytest

from django.contrib.auth import get_user_model

from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade


@pytest.mark.django_db
def test_send_grade_notification_email_missing_grade_returns_false():
    # Non-existent grade id should return False
    result = __import__('apps.notifications.tasks', fromlist=['']).send_grade_notification_email(999999)
    assert result is False


@pytest.mark.django_db
def test_send_grade_notification_email_student_no_email_handles_gracefully():
    User = get_user_model()
    teacher = User.objects.create_user(
        username='t_edge_teacher', email='t_edge@example.com', password='pass', role=User.UserRole.TEACHER
    )

    # student without email
    student = User.objects.create_user(
        username='t_edge_student', email='', password='pass', role=User.UserRole.STUDENT
    )

    course = Course.objects.create(
        name='Curso Edge', code='CEDGE1', academic_year=2025, semester=1, teacher=teacher
    )
    subject = Subject.objects.create(
        name='EdgeCase', code='EDGE101', course=course, teacher=teacher
    )
    CourseEnrollment.objects.create(student=student, course=course)
    grade = Grade.objects.create(student=student, subject=subject, value='2.0', graded_by=teacher)

    # Should not raise; depending on send_mail backend it may attempt to send to '' but task should return True
    result = __import__('apps.notifications.tasks', fromlist=['']).send_grade_notification_email(grade.id)
    assert result is True
