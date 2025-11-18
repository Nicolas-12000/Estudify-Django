import io
import json
from django.core.management import call_command
import pytest

from apps.courses.models import Course
from apps.users.models import User


@pytest.mark.django_db
def test_migrate_schedule_writes_failures_file(tmp_path):
    teacher = User.objects.create_user(username='f_teacher', password='pass', role=User.UserRole.TEACHER)
    # create a course with an invalid schedule entry to force a failure
    Course.objects.create(name='FailCourse', code='F1', academic_year=2025, semester=1, teacher=teacher)
    # Attach legacy schedule to the class for the test
    Course.schedule = 'InvalidEntry'

    out = io.StringIO()
    failures_path = tmp_path / 'failures.json'
    call_command('migrate_schedule', dry_run=True, failures_file=str(failures_path), stdout=out)

    # file should be created and contain a JSON list
    assert failures_path.exists()
    data = json.loads(failures_path.read_text(encoding='utf-8'))
    assert isinstance(data, list)
    assert len(data) >= 1

    # cleanup
    delattr(Course, 'schedule')
