import pytest
from django.core import mail
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from apps.notifications.tasks import send_welcome_email, send_grade_notification_email
from apps.academics.models import Grade
from apps.courses.models import Course, Subject

User = get_user_model()


@pytest.mark.django_db
def test_send_welcome_email_creates_notification(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    user = User.objects.create_user(username='n1', email='n1@example.com', password='p')
    # call task synchronously
    result = send_welcome_email(user.id)
    assert result is True
    # email was sent
    assert len(mail.outbox) == 1
    # notification created
    notifs = Notification.objects.filter(user=user)
    assert notifs.exists()


@pytest.mark.django_db
def test_send_grade_notification_creates_notification(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    teacher = User.objects.create_user(username='t1', email='t1@example.com', password='p', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='s1', email='s1@example.com', password='p', role=User.UserRole.STUDENT)
    course = Course.objects.create(name='C', code='C1', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='S', code='S1', credits=3, course=course, teacher=teacher)
    grade = Grade.objects.create(student=student, subject=subject, value=4.5, graded_by=teacher)
    result = send_grade_notification_email(grade.id)
    assert result is True
    assert len(mail.outbox) == 1
    notifs = Notification.objects.filter(user=student, notification_type='grade')
    assert notifs.exists()

# Create your tests here.
