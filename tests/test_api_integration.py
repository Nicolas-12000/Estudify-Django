from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.academics.models import Grade
from apps.courses.models import Course, CourseEnrollment, Subject

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture: Cliente de API."""
    return APIClient()


@pytest.fixture
def admin_user():
    """Fixture: Usuario administrador."""
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='admin123',
        role=User.UserRole.ADMIN,
        is_staff=True
    )
    return user


@pytest.fixture
def teacher_user():
    """Fixture: Usuario docente."""
    return User.objects.create_user(
        username='teacher',
        email='teacher@test.com',
        password='teacher123',
        first_name='Teacher',
        last_name='Test',
        role=User.UserRole.TEACHER
    )


@pytest.fixture
def student_user():
    """Fixture: Usuario estudiante."""
    return User.objects.create_user(
        username='student',
        email='student@test.com',
        password='student123',
        first_name='Student',
        last_name='Test',
        role=User.UserRole.STUDENT
    )


@pytest.mark.django_db
@pytest.mark.api
class TestUserAPI:
    """Tests para el endpoint de usuarios."""

    def test_list_users_authenticated(self, api_client, admin_user):
        """Test: Listar usuarios requiere autenticación."""
        # Sin autenticación
        response = api_client.get('/api/users/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Con autenticación
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/users/')
        assert response.status_code == status.HTTP_200_OK

    def test_get_current_user(self, api_client, student_user):
        """Test: Obtener información del usuario actual."""
        api_client.force_authenticate(user=student_user)
        response = api_client.get('/api/users/me/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'student'
        assert response.data['role'] == 'STUDENT'

    def test_create_user(self, api_client, admin_user):
        """Test: Crear nuevo usuario."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'STUDENT'
        }

        response = api_client.post('/api/users/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()

    def test_toggle_user_status(self, api_client, admin_user, student_user):
        """Test: Activar/desactivar usuario."""
        api_client.force_authenticate(user=admin_user)

        assert student_user.is_active

        response = api_client.post(
            f'/api/users/{student_user.id}/toggle_status/')
        assert response.status_code == status.HTTP_200_OK

        student_user.refresh_from_db()
        assert not student_user.is_active


@pytest.mark.django_db
@pytest.mark.api
class TestCourseAPI:
    """Tests para el endpoint de cursos."""

    def test_list_courses(self, api_client, teacher_user):
        """Test: Listar cursos."""
        # Crear curso
        Course.objects.create(
            name='Test Course',
            code='TST001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user
        )

        api_client.force_authenticate(user=teacher_user)
        response = api_client.get('/api/courses/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_course(self, api_client, teacher_user):
        """Test: Crear curso."""
        api_client.force_authenticate(user=teacher_user)

        data = {
            'name': 'New Course',
            'code': 'NEW001',
            'academic_year': 2025,
            'semester': 1,
            'teacher': teacher_user.id,
            'max_students': 30
        }

        response = api_client.post('/api/courses/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Course.objects.filter(code='NEW001').exists()

    def test_get_course_students(self, api_client, teacher_user, student_user):
        """Test: Obtener estudiantes de un curso."""
        # Crear curso e inscribir estudiante
        course = Course.objects.create(
            name='Test Course',
            code='TST001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user
        )
        CourseEnrollment.objects.create(
            student=student_user,
            course=course
        )

        api_client.force_authenticate(user=teacher_user)
        response = api_client.get(f'/api/courses/{course.id}/students/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['username'] == 'student'


@pytest.mark.django_db
@pytest.mark.api
class TestGradeAPI:
    """Tests para el endpoint de calificaciones."""

    @pytest.fixture
    def setup_grade_data(self, teacher_user, student_user):
        """Fixture: Configurar datos para calificaciones."""
        course = Course.objects.create(
            name='Test Course',
            code='TST001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user
        )
        subject = Subject.objects.create(
            name='Test Subject',
            code='TSUB001',
            course=course,
            teacher=teacher_user
        )
        enrollment = CourseEnrollment.objects.create(
            student=student_user,
            course=course
        )
        return {
            'course': course,
            'subject': subject,
            'enrollment': enrollment
        }

    def test_create_grade(
            self,
            api_client,
            teacher_user,
            student_user,
            setup_grade_data):
        """Test: Crear calificación."""
        api_client.force_authenticate(user=teacher_user)

        data = {
            'student': student_user.id,
            'subject': setup_grade_data['subject'].id,
            'value': '4.5',
            'grade_type': 'EXAM',
            'weight': '30.0',
            'comments': 'Excelente trabajo'
        }

        response = api_client.post('/api/grades/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Grade.objects.filter(student=student_user).exists()

    def test_grade_statistics(
            self,
            api_client,
            teacher_user,
            student_user,
            setup_grade_data):
        """Test: Obtener estadísticas de calificaciones."""
        # Crear algunas calificaciones
        subject = setup_grade_data['subject']
        for value in [4.5, 3.8, 4.0]:
            Grade.objects.create(
                student=student_user,
                subject=subject,
                value=Decimal(str(value)),
                grade_type='EXAM',
                weight=Decimal('30.0'),
                graded_by=teacher_user
            )

        api_client.force_authenticate(user=teacher_user)
        response = api_client.get('/api/grades/statistics/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

    def test_create_grade_without_enrollment_fails(
            self, api_client, teacher_user, student_user):
        """Test: No se puede crear calificación sin inscripción."""
        course = Course.objects.create(
            name='Test Course',
            code='TST001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user
        )
        subject = Subject.objects.create(
            name='Test Subject',
            code='TSUB001',
            course=course,
            teacher=teacher_user
        )

        api_client.force_authenticate(user=teacher_user)

        data = {
            'student': student_user.id,
            'subject': subject.id,
            'value': '4.5',
            'grade_type': 'EXAM',
            'weight': '30.0'
        }

        response = api_client.post('/api/grades/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.api
class TestEnrollmentAPI:
    """Tests para el endpoint de inscripciones."""

    def test_bulk_enrollment(self, api_client, teacher_user):
        """Test: Inscripción masiva de estudiantes."""
        # Crear curso
        course = Course.objects.create(
            name='Test Course',
            code='TST001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user,
            max_students=10
        )

        # Crear estudiantes
        students = []
        for i in range(3):
            student = User.objects.create_user(
                username=f'student{i}',
                password='pass123',
                role=User.UserRole.STUDENT
            )
            students.append(student.id)

        api_client.force_authenticate(user=teacher_user)

        data = {
            'course_id': course.id,
            'student_ids': students
        }

        response = api_client.post('/api/enrollments/bulk_enroll/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['enrolled_count'] == 3
        assert course.enrollments.count() == 3

    def test_enrollment_duplicate_fails(
            self, api_client, teacher_user, student_user):
        """Test: No se puede inscribir dos veces al mismo estudiante."""
        course = Course.objects.create(
            name='Test Course',
            code='TST001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user
        )

        api_client.force_authenticate(user=teacher_user)

        data = {
            'student': student_user.id,
            'course': course.id
        }

        # Primera inscripción
        response = api_client.post('/api/enrollments/', data)
        assert response.status_code == status.HTTP_201_CREATED

        # Segunda inscripción (debe fallar)
        response = api_client.post('/api/enrollments/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.integration
class TestFullWorkflow:
    """Tests de integración del flujo completo."""

    def test_complete_student_workflow(
            self, api_client, teacher_user, student_user):
        """Test: Flujo completo desde inscripción hasta calificación."""
        # 1. Crear curso
        course = Course.objects.create(
            name='Integration Test Course',
            code='INT001',
            academic_year=2025,
            semester=1,
            teacher=teacher_user
        )

        # 2. Crear materia
        subject = Subject.objects.create(
            name='Integration Subject',
            code='INTSUB001',
            course=course,
            teacher=teacher_user
        )

        # 3. Inscribir estudiante
        CourseEnrollment.objects.create(
            student=student_user,
            course=course
        )

        # 4. Crear calificación
        api_client.force_authenticate(user=teacher_user)
        grade_data = {
            'student': student_user.id,
            'subject': subject.id,
            'value': '4.5',
            'grade_type': 'EXAM',
            'weight': '40.0'
        }
        response = api_client.post('/api/grades/', grade_data)
        assert response.status_code == status.HTTP_201_CREATED

        # 5. Verificar calificación
        api_client.force_authenticate(user=student_user)
        response = api_client.get(f'/api/grades/?student={student_user.id}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert float(response.data['results'][0]['value']) == 4.5
