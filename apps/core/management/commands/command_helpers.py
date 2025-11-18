import os
from typing import Iterable, List, Optional, Tuple

from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from apps.courses.models import Subject, CourseEnrollment
from apps.academics.models import Grade, Attendance

User = get_user_model()


def env_or_default(key: str, default: str) -> str:
    return os.environ.get(key, default)


def create_superuser_if_missing(
    username: str,
    email: str,
    password: str,
    stdout,
    stderr,
    style,
) -> Tuple[bool, str]:
    """Create a superuser if it does not exist. Returns (created, username)."""
    if not User.objects.filter(username=username).exists():
        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            stdout.write(style.SUCCESS(f'Created superuser: {username}'))
            return True, username
        except Exception as exc:
            stderr.write(f'Could not create superuser {username}: {exc}')
            return False, username
    else:
        stdout.write(f'Superuser {username} already exists')
        return False, username


def create_user_if_missing(username: str, email: str, password: str,
                           set_staff: bool = False, set_superuser: bool = False,
                           role_attr: Optional[str] = None, role_value=None,
                           stdout=None, stderr=None, style=None) -> Tuple[bool, object]:
    """Create a regular user if missing. Returns (created, user).

    role_attr/role_value: if given, attempts to set attribute on model (e.g., is_teacher)
    """
    user = None
    created = False
    if not User.objects.filter(username=username).exists():
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            # Apply flags and role attributes in a helper to reduce complexity
            _apply_user_flags(user, role_attr, role_value, set_staff, set_superuser)
            user.save()
            created = True
            if stdout and style:
                stdout.write(style.SUCCESS(f'Created user: {username}'))
        except Exception as exc:
            if stderr:
                stderr.write(f'Could not create user {username}: {exc}')
    else:
        user = User.objects.get(username=username)
        if stdout:
            stdout.write(f'User {username} already exists')

    return created, user


def _apply_user_flags(user, role_attr: Optional[str], role_value, set_staff: bool, set_superuser: bool):
    """Apply role flags and staff/superuser flags to the user instance."""
    # Support mapping boolean-like property names (e.g. 'is_teacher') to the
    # normalized `role` CharField on the custom User model. Some of the
    # `is_*` helpers are properties without setters and attempting to
    # `setattr` raised "property has no setter" errors when the seed tried
    # to assign them. Detect common names and set `user.role` safely instead.
    if role_attr:
        mapped = False
        if isinstance(role_attr, str) and role_attr.startswith('is_'):
            # map property name to role value on the User model
            try:
                user_model = type(user)
                # access the UserRole enum if available, otherwise fall back to strings
                if hasattr(user_model, 'UserRole'):
                    mapping = {
                        'is_teacher': user_model.UserRole.TEACHER,
                        'is_student': user_model.UserRole.STUDENT,
                        'is_admin': user_model.UserRole.ADMIN,
                    }
                    if role_attr in mapping:
                        user.role = mapping[role_attr]
                        mapped = True
            except Exception:
                mapped = False
        # if not mapped to the role field, fall back to setting attribute when possible
        if not mapped and hasattr(user, role_attr):
            setattr(user, role_attr, role_value if role_value is not None else True)
    if set_staff:
        user.is_staff = True
    if set_superuser:
        user.is_superuser = True


def normalize_user_tuples(data: Iterable[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """Ensure the sequence of (username, first_name, last_name) tuples is a list."""
    return list(data)


def create_subjects_for_course(course, subject_infos):
    """Create Subject objects for a given course.

    subject_infos: iterable of (code, name, credits, teacher)
    Returns list of Subject instances.
    """
    subjects = []
    for info in subject_infos:
        # allow tuples of different lengths
        if len(info) == 2:
            code, name = info
            credits = 0
            teacher = None
        elif len(info) == 3:
            code, name, credits = info
            teacher = None
        else:
            code, name, credits, teacher = info

        subject, _ = Subject.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'credits': credits,
                'course': course,
                'teacher': teacher,
            }
        )
        subjects.append(subject)
    return subjects


def enroll_students_in_course(course, students):
    """Enroll students in a course. Returns list of CourseEnrollment instances."""
    enrollments = []
    for student in students:
        enrollment, _ = CourseEnrollment.objects.get_or_create(
            student=student,
            course=course,
        )
        enrollments.append(enrollment)
    return enrollments


def create_grades_for_subjects(subjects, students, graded_by=None, value=Decimal('4.0')):
    """Create a simple grade record for each student-subject pair.

    This helper is deterministic (same `value`) so tests remain stable.
    Returns list of Grade instances.
    """
    grades = []
    for subject in subjects:
        for student in students:
            grade, _ = Grade.objects.get_or_create(
                student=student,
                subject=subject,
                defaults={
                    'value': value,
                    'grade_type': 'EXAM',
                    'weight': Decimal('100.00'),
                    'graded_by': graded_by,
                }
            )
            grades.append(grade)
    return grades


def create_attendance_for_course(course, students, days=3, recorded_by=None):
    """Create attendance records for the last `days` days for each student.

    Returns list of Attendance instances.
    """
    records = []
    today = date.today()
    for d in range(days):
        day = today - timedelta(days=d)
        for student in students:
            attendance, _ = Attendance.objects.get_or_create(
                student=student,
                course=course,
                date=day,
                defaults={
                    'status': Attendance.AttendanceStatus.PRESENT,
                    'recorded_by': recorded_by,
                }
            )
            records.append(attendance)
    return records
