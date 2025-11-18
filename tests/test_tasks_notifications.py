from unittest import mock

import pytest

from django.contrib.auth import get_user_model

from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade
from apps.notifications.models import Notification
from apps.notifications.tasks import send_welcome_email, send_grade_notification_email


@pytest.mark.django_db
def test_send_welcome_email_creates_notification_and_sends_mail(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    User = get_user_model()
    user = User.objects.create_user(username='u1', email='u1@example.com', password='pass')

    with mock.patch('apps.notifications.tasks.send_mail') as mocked_send:
        result = send_welcome_email(user.id)
        assert result is True
        mocked_send.assert_called()

    # Verify notification created
    assert Notification.objects.filter(user=user, title__icontains='Bienvenido').exists()


@pytest.mark.django_db
def test_send_grade_notification_email_creates_notification_and_sends_mail():
    User = get_user_model()
    teacher = User.objects.create_user(
        username='t1', email='t1@example.com', password='pass', role=User.UserRole.TEACHER
    )
    student = User.objects.create_user(
        username='s1', email='s1@example.com', password='pass', role=User.UserRole.STUDENT
    )

    course = Course.objects.create(name='Curso 1', code='C1', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Matematicas', code='MATH101', course=course, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course)

    grade = Grade.objects.create(student=student, subject=subject, value='4.0', graded_by=teacher)

    with mock.patch('apps.notifications.tasks.send_mail') as mock_send:
        result = send_grade_notification_email(grade.id)
        assert result is True
        mock_send.assert_called_once()

    # Check a notification was created for the student referencing the grade
    assert Notification.objects.filter(user=student, object_id=grade.id, notification_type='grade').exists()
