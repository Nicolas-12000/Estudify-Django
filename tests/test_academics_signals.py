import pytest
from unittest.mock import patch

from django.contrib.auth import get_user_model

from apps.courses.models import Course, Subject
from apps.academics.models import Grade


@pytest.mark.django_db
def test_notify_student_on_grade_creation_triggers_task():
    User = get_user_model()
    student = User.objects.create_user(
        username='stud', email='s@example.com', password='p',
        role=User.UserRole.STUDENT,
    )

    course = Course.objects.create(name='Curso A', code='CURA', academic_year=2025, semester=1)
    subject = Subject.objects.create(name='Materia A', code='MAT-A', course=course)

    with patch('apps.notifications.tasks.send_grade_notification_email.delay') as mock_delay:
        grade = Grade.objects.create(student=student, subject=subject, value='4.5')
        # signal should import the task and call .delay with the new grade id
        mock_delay.assert_called()
        called_args = mock_delay.call_args[0]
        assert called_args[0] == grade.id


@pytest.mark.django_db
def test_notify_student_signal_handles_task_exception():
    """If the task's .delay raises, the signal should swallow the exception."""
    User = get_user_model()
    student = User.objects.create_user(
        username='stud2', email='s2@example.com', password='p',
        role=User.UserRole.STUDENT,
    )

    course = Course.objects.create(name='Curso B', code='CURB', academic_year=2025, semester=1)
    subject = Subject.objects.create(name='Materia B', code='MAT-B', course=course)

    with patch('apps.notifications.tasks.send_grade_notification_email.delay', side_effect=Exception('boom')) as mock_delay:
        # Should not raise despite .delay raising internally
        Grade.objects.create(student=student, subject=subject, value='3.7')
        assert mock_delay.called


@pytest.mark.django_db
def test_notify_student_via_update_or_create_triggers_task():
    User = get_user_model()
    student = User.objects.create_user(
        username='stud3', email='s3@example.com', password='p',
        role=User.UserRole.STUDENT,
    )

    course = Course.objects.create(name='Curso C', code='CURC', academic_year=2025, semester=1)
    subject = Subject.objects.create(name='Materia C', code='MAT-C', course=course)

    with patch('apps.notifications.tasks.send_grade_notification_email.delay') as mock_delay:
        grade, created = Grade.objects.update_or_create(
            student=student, subject=subject, defaults={'value': '4.2'}
        )
        assert created is True
        assert mock_delay.called
