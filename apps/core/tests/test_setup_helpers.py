import pytest
from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.courses.models import Course
from apps.core.management.commands.command_helpers import (
    create_subjects_for_course, enroll_students_in_course,
    create_grades_for_subjects, create_attendance_for_course)

User = get_user_model()


@pytest.mark.django_db
def test_create_subjects_and_enrollments():
    teacher = User.objects.create_user(username='t1', password='pass', role=User.UserRole.TEACHER)
    course = Course.objects.create(name='Test Course', code='TC101', academic_year=2025, semester=1, teacher=teacher)

    subjects = create_subjects_for_course(course, [
        ('S1', 'Subject 1', 3, teacher),
        ('S2', 'Subject 2', 2, teacher),
    ])
    assert len(subjects) == 2
    assert all(s.course_id == course.id for s in subjects)

    # create students
    students = [User.objects.create_user(username=f's{i}', password='p', role=User.UserRole.STUDENT) for i in range(3)]
    enrollments = enroll_students_in_course(course, students)
    assert len(enrollments) == 3
    assert all(e.course_id == course.id for e in enrollments)


@pytest.mark.django_db
def test_create_grades_and_attendance():
    teacher = User.objects.create_user(username='t2', password='pass', role=User.UserRole.TEACHER)
    course = Course.objects.create(name='Course B', code='CB202', academic_year=2025, semester=1, teacher=teacher)
    subjects = create_subjects_for_course(course, [('S3', 'Subject 3', 3, teacher)])
    students = [User.objects.create_user(username=f'sg{i}', password='p', role=User.UserRole.STUDENT) for i in range(2)]
    enroll_students_in_course(course, students)

    grades = create_grades_for_subjects(subjects, students, graded_by=teacher, value=Decimal('4.5'))
    assert len(grades) == len(subjects) * len(students)
    assert all(g.graded_by_id == teacher.id for g in grades)

    records = create_attendance_for_course(course, students, days=2, recorded_by=teacher)
    assert len(records) == 2 * len(students)
    assert all(r.course_id == course.id for r in records)
