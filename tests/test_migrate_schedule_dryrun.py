import io
from django.core.management import call_command
import pytest

from apps.courses.models import Course, TimeSlot, CourseSession
from apps.users.models import User


@pytest.mark.django_db
def test_migrate_schedule_dry_run_reports_changes_but_does_not_write(db):
    teacher = User.objects.create_user(username='dry_teacher', password='pass', role=User.UserRole.TEACHER)
    # legacy schedule string with two entries
    Course.objects.create(
        name='DryRunCourse', code='DR1', academic_year=2025, semester=1, teacher=teacher
    )
    # The legacy `schedule` field was removed from the model in newer migrations.
    # For testing the management command we attach a temporary class attribute so
    # `getattr(course, 'schedule', '')` inside the command returns the legacy text.
    Course.schedule = 'Lun 8-10; Mar 9-11'

    # Ensure no timeslots or sessions exist
    assert TimeSlot.objects.count() == 0
    assert CourseSession.objects.count() == 0

    out = io.StringIO()
    # run dry-run
    call_command('migrate_schedule', dry_run=True, stdout=out)
    output = out.getvalue()

    # In dry-run mode we expect the command to state it is in dry-run
    assert 'Modo dry-run' in output

    # The DB should still be unchanged
    assert TimeSlot.objects.count() == 0
    assert CourseSession.objects.count() == 0

    # But the output should report created sessions (simulated)
    assert 'Sessions creadas' in output

    # Clean up the temporary attribute to avoid affecting other tests
    delattr(Course, 'schedule')
