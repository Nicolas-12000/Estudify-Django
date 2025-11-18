import pytest
from django.contrib.auth import get_user_model

from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade
from apps.notifications.models import Notification
from apps.notifications.tasks import send_grade_notification_email


@pytest.mark.django_db
def test_send_grade_notification_idempotent():
    User = get_user_model()
    teacher = User.objects.create_user(username='tid', email='t@id.test', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='sid', email='s@id.test', password='p', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='Curso ID', code='CID', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='Sub ID', code='SID', course=course, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course)

    grade = Grade.objects.create(student=student, subject=subject, value='5.0', graded_by=teacher)

    # Call task twice simulating duplicate enqueues
    res1 = send_grade_notification_email(grade.id)
    res2 = send_grade_notification_email(grade.id)

    assert res1 is True and res2 is True
    # Only one notification must exist for this grade and student
    notes = Notification.objects.filter(user=student, notification_type='grade', object_id=grade.id)
    assert notes.count() == 1
