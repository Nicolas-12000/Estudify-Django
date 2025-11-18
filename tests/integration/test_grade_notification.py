import time

import pytest

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.academics.models import Grade
from apps.courses.models import Course, Subject, CourseEnrollment
from apps.notifications.models import Notification
from apps.notifications.tasks import send_grade_notification_email

# Use a test-scoped Celery worker so the test doesn't need an external worker
from celery.contrib.testing.worker import start_worker
from config.celery import app as celery_app


@pytest.mark.django_db(transaction=True)
def test_enqueue_grade_notification_and_worker_processes():
    """Enqueue a grade notification task and poll for a Notification created by the worker.

    Intended to run in CI where a Celery worker + Redis are available.
    """
    # We run a test-scoped worker below so no external worker is required.

    User = get_user_model()
    teacher = User.objects.create_user(
        username='it_teacher', email='it_teacher@example.com', password='pass', role=User.UserRole.TEACHER,
    )
    student = User.objects.create_user(
        username='it_student', email='it_student@example.com', password='pass', role=User.UserRole.STUDENT,
    )

    course = Course.objects.create(
        name='Curso IT', code='CIT1', academic_year=2025, semester=1, teacher=teacher
    )
    subject = Subject.objects.create(
        name='Integracion', code='INT101', course=course, teacher=teacher
    )
    CourseEnrollment.objects.create(student=student, course=course)
    grade = Grade.objects.create(student=student, subject=subject, value='3.5', graded_by=teacher)

    # Commit so the worker can see the created objects when using a separate DB transaction
    transaction.commit()

    # Start a test-scoped worker that uses the same Celery app/settings
    with start_worker(celery_app, pool='solo', perform_ping_check=False):
        # Enqueue the Celery task
        send_grade_notification_email.delay(grade.id)

        # Poll for notification (timeout configurable if needed)
        timeout = 20
        interval = 0.5
        deadline = time.time() + timeout
        found = False
        while time.time() < deadline:
            if Notification.objects.filter(user=student, object_id=grade.id, notification_type='grade').exists():
                found = True
                break
            time.sleep(interval)

    assert found, 'Grade notification not created by Celery worker within timeout'
