import pytest
from datetime import date

from django.contrib.auth import get_user_model

from apps.academics.forms import (
    GradeForm, AttendanceForm, BulkAttendanceForm, GradeFilterForm
)
from apps.courses.models import Course, Subject, CourseEnrollment


User = get_user_model()


@pytest.mark.django_db
def test_gradeform_clean_raises_when_student_not_enrolled():
    teacher = User.objects.create_user(username='t1', password='pass', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='s1', password='pass', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='C1', code='C1', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='S1', code='S1', course=course, teacher=teacher)

    data = {
        'student': student.pk,
        'subject': subject.pk,
        'value': '4.0',
        'grade_type': 'EXAM',
        'weight': '100.00',
        'comments': ''
    }

    form = GradeForm(data=data, teacher=teacher)
    assert not form.is_valid()
    assert '__all__' in form.errors or 'student' in form.errors


@pytest.mark.django_db
def test_gradeform_valid_when_student_enrolled():
    teacher = User.objects.create_user(username='t2', password='pass', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='s2', password='pass', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='C2', code='C2', academic_year=2025, semester=1, teacher=teacher)
    subject = Subject.objects.create(name='S2', code='S2', course=course, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course)

    data = {
        'student': student.pk,
        'subject': subject.pk,
        'value': '3.5',
        'grade_type': 'EXAM',
        'weight': '100.00',
        'comments': ''
    }

    form = GradeForm(data=data, teacher=teacher)
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_attendanceform_clean_raises_when_not_enrolled():
    teacher = User.objects.create_user(username='t3', password='pass', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='s3', password='pass', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='C3', code='C3', academic_year=2025, semester=1, teacher=teacher)

    data = {
        'student': student.pk,
        'course': course.pk,
        'date': date.today().isoformat(),
        'status': 'PRESENT',
        'notes': ''
    }

    form = AttendanceForm(data=data, teacher=teacher)
    assert not form.is_valid()
    assert '__all__' in form.errors or 'student' in form.errors


@pytest.mark.django_db
def test_attendanceform_valid_when_enrolled():
    teacher = User.objects.create_user(username='t4', password='pass', role=User.UserRole.TEACHER)
    student = User.objects.create_user(username='s4', password='pass', role=User.UserRole.STUDENT)

    course = Course.objects.create(name='C4', code='C4', academic_year=2025, semester=1, teacher=teacher)
    CourseEnrollment.objects.create(student=student, course=course)

    data = {
        'student': student.pk,
        'course': course.pk,
        'date': date.today().isoformat(),
        'status': 'PRESENT',
        'notes': ''
    }

    form = AttendanceForm(data=data, teacher=teacher)
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_bulkattendance_filters_courses_for_teacher():
    teacher = User.objects.create_user(username='t5', password='pass', role=User.UserRole.TEACHER)
    other_teacher = User.objects.create_user(username='t6', password='pass', role=User.UserRole.TEACHER)

    c1 = Course.objects.create(name='C5', code='C5', academic_year=2025, semester=1, teacher=teacher)
    c2 = Course.objects.create(name='C6', code='C6', academic_year=2025, semester=1, teacher=other_teacher)

    form = BulkAttendanceForm(teacher=teacher)
    qs = form.fields['course'].queryset
    assert c1 in qs
    assert c2 not in qs


@pytest.mark.django_db
def test_gradefilterform_has_grade_type_choices():
    form = GradeFilterForm()
    # grade_type choices should include 'EXAM'
    choices = form.fields['grade_type'].choices
    assert any(c[0] == 'EXAM' for c in choices)
