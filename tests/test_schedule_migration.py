import pytest
from apps.courses.models import Course, TimeSlot, Classroom, CourseSession
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_create_sessions_and_timeslots(db):
    teacher = User.objects.create_user(username='t1', password='pass', role=User.UserRole.TEACHER)
    course = Course.objects.create(name='Curso A', code='CA1', academic_year=2025, semester=1, teacher=teacher)

    # create timeslots and classroom, then sessions
    ts1 = TimeSlot.objects.create(day_of_week=0, start_time='08:00', end_time='10:00')
    ts2 = TimeSlot.objects.create(day_of_week=2, start_time='10:00', end_time='12:00')
    room = Classroom.objects.create(name='Aula 1')
    CourseSession.objects.create(course=course, timeslot=ts1, classroom_fk=room)
    CourseSession.objects.create(course=course, timeslot=ts2, classroom_fk=room)

    assert TimeSlot.objects.count() >= 2
    assert Classroom.objects.filter(name='Aula 1').exists()
    assert CourseSession.objects.filter(course=course).count() == 2


def test_course_session_overlap_validation(db):
    teacher = User.objects.create_user(username='t2', password='pass', role=User.UserRole.TEACHER)
    course1 = Course.objects.create(name='C1', code='C1', academic_year=2025, semester=1, teacher=teacher)
    course2 = Course.objects.create(name='C2', code='C2', academic_year=2025, semester=1, teacher=teacher)

    ts1 = TimeSlot.objects.create(day_of_week=0, start_time='08:00', end_time='10:00')
    ts2 = TimeSlot.objects.create(day_of_week=0, start_time='09:00', end_time='11:00')
    room = Classroom.objects.create(name='A1')

    CourseSession.objects.create(course=course1, timeslot=ts1, classroom_fk=room)

    s2 = CourseSession(course=course2, timeslot=ts2, classroom_fk=room)
    with pytest.raises(Exception):
        s2.full_clean()
