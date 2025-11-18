import pytest

from django.contrib.auth import get_user_model

from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade
from apps.notifications.models import Notification


@pytest.mark.django_db
def test_grade_creation_triggers_notification_eager_celery(settings):
    """Integration-style test: with Celery eager mode, creating a Grade should
    cause the signal to enqueue the task which will run immediately, creating
    a Notification for the student.
    """
    # Ensure tasks run synchronously during test
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    User = get_user_model()
    teacher = User.objects.create_user(username='t_e2e', email='t@e2e.test', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='s_e2e', email='s@e2e.test', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso E2E', code='E2E1', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Materia E2E', code='ME2E', course=course, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course)

    # Create grade; the post_save signal should call send_grade_notification_email.delay()
    grade = Grade.objects.create(student=student, subject=subject, value='4.7', graded_by=teacher)

    # Because CELERY_TASK_ALWAYS_EAGER=True the task should run synchronously
    assert Notification.objects.filter(user=student, object_id=grade.id, notification_type='grade').exists()
