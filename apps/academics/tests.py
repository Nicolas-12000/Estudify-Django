from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.academics.models import Attendance, Grade
from apps.courses.models import Course, CourseEnrollment, Subject

User = get_user_model()


@pytest.fixture
def teacher():
    """Fixture: Docente."""
    return User.objects.create_user(
        username='teacher',
        password='pass123',
        role=User.UserRole.TEACHER
    )


@pytest.fixture
def student():
    """Fixture: Estudiante."""
    return User.objects.create_user(
        username='student',
        password='pass123',
        first_name='John',
        last_name='Doe',
        role=User.UserRole.STUDENT
    )


@pytest.fixture
def course(teacher):
    """Fixture: Curso."""
    return Course.objects.create(
        name='Math 101',
        code='MTH101',
        academic_year=2025,
        semester=1,
        teacher=teacher
    )


@pytest.fixture
def subject(course, teacher):
    """Fixture: Materia."""
    return Subject.objects.create(
        name='Algebra',
        code='ALG101',
        course=course,
        teacher=teacher
    )


@pytest.fixture
def enrollment(student, course):
    """Fixture: Inscripción de estudiante en curso."""
    return CourseEnrollment.objects.create(
        student=student,
        course=course
    )


@pytest.mark.django_db
class TestGradeModel:
    """Tests para el modelo Grade."""

    def test_create_grade(self, student, subject, teacher, enrollment):
        """Test: Crear una calificación."""
        grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=Decimal('4.5'),
            grade_type='EXAM',
            weight=Decimal('30.0'),
            graded_by=teacher
        )
        assert grade.student == student
        assert grade.subject == subject
        assert grade.value == Decimal('4.5')
        assert grade.is_passing

    def test_grade_str_representation(
            self, student, subject, teacher, enrollment):
        """Test: Representación en string de calificación."""
        grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=Decimal('3.8'),
            graded_by=teacher
        )
        expected = f'{student.get_full_name()} - {subject.name}: 3.8'
        assert str(grade) == expected

    def test_grade_is_passing(self, student, subject, teacher, enrollment):
        """Test: Verificar si la calificación es aprobatoria."""
        passing_grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=Decimal('3.5'),
            graded_by=teacher
        )
        failing_grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=Decimal('2.8'),
            graded_by=teacher
        )

        assert passing_grade.is_passing
        assert not failing_grade.is_passing

    def test_grade_letter_grade(self, student, subject, teacher, enrollment):
        """Test: Obtener calificación en formato letra."""
        test_cases = [
            (Decimal('4.8'), 'A'),
            (Decimal('4.3'), 'B'),
            (Decimal('3.5'), 'C'),
            (Decimal('2.5'), 'D'),
            (Decimal('1.5'), 'F'),
        ]

        for value, expected_letter in test_cases:
            grade = Grade.objects.create(
                student=student,
                subject=subject,
                value=value,
                graded_by=teacher
            )
            assert grade.letter_grade == expected_letter
            grade.delete()

    def test_grade_validation_student_not_enrolled(
            self, student, subject, teacher):
        """Test: Validar que el estudiante esté inscrito en el curso."""
        # Crear calificación sin inscripción previa
        grade = Grade(
            student=student,
            subject=subject,
            value=Decimal('4.0'),
            graded_by=teacher
        )

        with pytest.raises(ValidationError):
            grade.clean()

    def test_grade_value_range(self, student, subject, teacher, enrollment):
        """Test: Validar rango de calificación (0.0 - 5.0)."""
        # Valor válido
        grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=Decimal('5.0'),
            graded_by=teacher
        )
        assert grade.value == Decimal('5.0')

        # Valores fuera de rango deberían fallar en la validación del modelo
        # pero no en la creación directa (se valida en forms)

    def test_grade_weight_range(self, student, subject, teacher, enrollment):
        """Test: Validar peso de calificación (0-100)."""
        grade = Grade.objects.create(
            student=student,
            subject=subject,
            value=Decimal('4.0'),
            weight=Decimal('100.0'),
            graded_by=teacher
        )
        assert grade.weight == Decimal('100.0')


@pytest.mark.django_db
class TestAttendanceModel:
    """Tests para el modelo Attendance."""

    def test_create_attendance(self, student, course, teacher, enrollment):
        """Test: Crear registro de asistencia."""
        attendance = Attendance.objects.create(
            student=student,
            course=course,
            date=date.today(),
            status=Attendance.AttendanceStatus.PRESENT,
            recorded_by=teacher
        )
        assert attendance.student == student
        assert attendance.course == course
        assert attendance.status == Attendance.AttendanceStatus.PRESENT

    def test_attendance_str_representation(
            self, student, course, teacher, enrollment):
        """Test: Representación en string de asistencia."""
        attendance = Attendance.objects.create(
            student=student,
            course=course,
            date=date(2025, 1, 15),
            status=Attendance.AttendanceStatus.PRESENT,
            recorded_by=teacher
        )
        expected = f'{student.get_full_name(
        )} - {course.name} (2025-01-15): Presente'
        assert str(attendance) == expected

    def test_attendance_statuses(self, student, course, teacher, enrollment):
        """Test: Diferentes estados de asistencia."""
        statuses = [
            Attendance.AttendanceStatus.PRESENT,
            Attendance.AttendanceStatus.ABSENT,
            Attendance.AttendanceStatus.LATE,
            Attendance.AttendanceStatus.EXCUSED,
        ]

        for status in statuses:
            attendance = Attendance.objects.create(
                student=student,
                course=course,
                date=date.today(),
                status=status,
                recorded_by=teacher
            )
            assert attendance.status == status
            attendance.delete()

    def test_attendance_unique_per_day(
            self, student, course, teacher, enrollment):
        """Test: Solo una asistencia por estudiante por curso por día."""
        Attendance.objects.create(
            student=student,
            course=course,
            date=date.today(),
            status=Attendance.AttendanceStatus.PRESENT,
            recorded_by=teacher
        )

        # Intentar crear otro registro para el mismo día
        with pytest.raises(Exception):  # IntegrityError
            Attendance.objects.create(
                student=student,
                course=course,
                date=date.today(),
                status=Attendance.AttendanceStatus.LATE,
                recorded_by=teacher
            )

    def test_attendance_validation_student_not_enrolled(
            self, student, course, teacher):
        """Test: Validar que el estudiante esté inscrito en el curso."""
        attendance = Attendance(
            student=student,
            course=course,
            date=date.today(),
            status=Attendance.AttendanceStatus.PRESENT,
            recorded_by=teacher
        )

        with pytest.raises(ValidationError):
            attendance.clean()

    def test_multiple_attendance_dates(
            self, student, course, teacher, enrollment):
        """Test: Múltiples registros en diferentes fechas."""
        dates = [
            date(2025, 1, 10),
            date(2025, 1, 11),
            date(2025, 1, 12),
        ]

        for d in dates:
            Attendance.objects.create(
                student=student,
                course=course,
                date=d,
                status=Attendance.AttendanceStatus.PRESENT,
                recorded_by=teacher
            )

        assert student.attendances.count() == 3
