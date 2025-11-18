import pytest
from django.contrib.auth import get_user_model

from apps.courses.models import Course, CourseEnrollment, Subject

User = get_user_model()


@pytest.fixture
def teacher():
    """Fixture: Crear un docente."""
    return User.objects.create_user(
        username='teacher1',
        email='teacher@example.com',
        password='pass123',
        first_name='Teacher',
        last_name='One',
        role=User.UserRole.TEACHER
    )


@pytest.fixture
def student():
    """Fixture: Crear un estudiante."""
    return User.objects.create_user(
        username='student1',
        email='student@example.com',
        password='pass123',
        first_name='Student',
        last_name='One',
        role=User.UserRole.STUDENT
    )


@pytest.fixture
def course(teacher):
    """Fixture: Crear un curso."""
    return Course.objects.create(
        name='Matemáticas 11A',
        code='MAT11A',
        academic_year=2025,
        semester=1,
        teacher=teacher,
        max_students=30
    )


@pytest.mark.django_db
class TestCourseModel:
    """Tests para el modelo Course."""

    def test_create_course(self, teacher):
        """Test: Crear un curso."""
        course = Course.objects.create(
            name='Física 10B',
            code='FIS10B',
            description='Curso de física',
            academic_year=2025,
            semester=2,
            teacher=teacher,
            max_students=25
        )
        assert course.name == 'Física 10B'
        assert course.code == 'FIS10B'
        assert course.teacher == teacher
        assert course.is_active

    def test_course_str_representation(self, course):
        """Test: Representación en string del curso."""
        expected = 'Matemáticas 11A (2025-1)'
        assert str(course) == expected

    def test_course_unique_code_per_period(self, teacher):
        """Test: El código debe ser único por periodo académico."""
        Course.objects.create(
            name='Curso 1',
            code='MAT101',
            academic_year=2025,
            semester=1,
            teacher=teacher
        )

        # Mismo código, mismo periodo -> Error
        with pytest.raises(Exception):  # IntegrityError
            Course.objects.create(
                name='Curso 2',
                code='MAT101',
                academic_year=2025,
                semester=1,
                teacher=teacher
            )

    def test_course_enrolled_count(self, course, student):
        """Test: Contar estudiantes inscritos."""
        assert course.enrolled_count == 0

        CourseEnrollment.objects.create(
            student=student,
            course=course
        )

        assert course.enrolled_count == 1

    def test_course_is_full(self, course):
        """Test: Verificar si el curso está lleno."""
        course.max_students = 2
        course.save()

        assert not course.is_full

        # Inscribir 2 estudiantes
        for i in range(2):
            student = User.objects.create_user(
                username=f'student{i}',
                password='pass123',
                role=User.UserRole.STUDENT
            )
            CourseEnrollment.objects.create(
                student=student,
                course=course
            )

        assert course.is_full


@pytest.mark.django_db
class TestSubjectModel:
    """Tests para el modelo Subject."""

    def test_create_subject(self, course, teacher):
        """Test: Crear una materia."""
        subject = Subject.objects.create(
            name='Álgebra',
            code='ALG101',
            description='Álgebra básica',
            credits=4,
            course=course,
            teacher=teacher
        )
        assert subject.name == 'Álgebra'
        assert subject.course == course
        assert subject.credits == 4

    def test_subject_str_representation(self, course, teacher):
        """Test: Representación en string de la materia."""
        subject = Subject.objects.create(
            name='Geometría',
            code='GEO101',
            course=course,
            teacher=teacher
        )
        expected = f'Geometría - {course.name}'
        assert str(subject) == expected

    def test_subject_unique_code(self, course, teacher):
        """Test: El código de materia debe ser único."""
        Subject.objects.create(
            name='Materia 1',
            code='MAT001',
            course=course,
            teacher=teacher
        )

        # Crear otra materia con el mismo código
        with pytest.raises(Exception):  # IntegrityError
            Subject.objects.create(
                name='Materia 2',
                code='MAT001',
                course=course,
                teacher=teacher
            )

    def test_subject_cascade_delete_with_course(self, course, teacher):
        """Test: Eliminar curso elimina sus materias."""
        subject = Subject.objects.create(
            name='Test Subject',
            code='TST001',
            course=course,
            teacher=teacher
        )

        course.id
        course.delete()

        # Verificar que la materia fue eliminada
        assert not Subject.objects.filter(id=subject.id).exists()


@pytest.mark.django_db
class TestCourseEnrollmentModel:
    """Tests para el modelo CourseEnrollment."""

    def test_create_enrollment(self, student, course):
        """Test: Inscribir estudiante en curso."""
        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course
        )
        assert enrollment.student == student
        assert enrollment.course == course
        assert enrollment.is_active

    def test_enrollment_str_representation(self, student, course):
        """Test: Representación en string de inscripción."""
        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course
        )
        expected = f'{student.get_full_name()} - {course.name}'
        assert str(enrollment) == expected

    def test_enrollment_unique_constraint(self, student, course):
        """Test: Un estudiante no puede inscribirse dos veces en el mismo curso."""
        CourseEnrollment.objects.create(
            student=student,
            course=course
        )

        # Intentar inscribir nuevamente
        with pytest.raises(Exception):  # IntegrityError
            CourseEnrollment.objects.create(
                student=student,
                course=course
            )

    def test_multiple_students_same_course(self, course):
        """Test: Múltiples estudiantes pueden inscribirse en el mismo curso."""
        students = []
        for i in range(3):
            student = User.objects.create_user(
                username=f'student{i}',
                password='pass123',
                role=User.UserRole.STUDENT
            )
            students.append(student)
            CourseEnrollment.objects.create(
                student=student,
                course=course
            )

        assert course.enrollments.count() == 3

    def test_student_multiple_courses(self, student, teacher):
        """Test: Un estudiante puede inscribirse en múltiples cursos."""
        courses = []
        for i in range(3):
            course = Course.objects.create(
                name=f'Course {i}',
                code=f'CRS{i}',
                academic_year=2025,
                semester=1,
                teacher=teacher
            )
            courses.append(course)
            CourseEnrollment.objects.create(
                student=student,
                course=course
            )

        assert student.enrollments.count() == 3
