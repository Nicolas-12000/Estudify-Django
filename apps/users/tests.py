import pytest
from django.contrib.auth import get_user_model

from apps.users.models import Profile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests para el modelo User."""

    def test_create_user(self):
        """Test: Crear usuario básico."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.role == User.UserRole.STUDENT  # Default role

    def test_create_teacher(self):
        """Test: Crear usuario con rol de docente."""
        teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='pass123',
            role=User.UserRole.TEACHER
        )
        assert teacher.is_teacher
        assert not teacher.is_student
        assert not teacher.is_admin_role

    def test_create_admin(self):
        """Test: Crear usuario administrador."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role=User.UserRole.ADMIN
        )
        assert admin.is_admin_role
        assert admin.is_staff
        assert admin.is_superuser

    def test_get_full_name(self):
        """Test: Obtener nombre completo del usuario."""
        user = User.objects.create_user(
            username='john',
            first_name='John',
            last_name='Doe',
            password='pass123'
        )
        assert user.get_full_name() == 'John Doe'

    def test_get_full_name_without_names(self):
        """Test: get_full_name retorna username si no hay nombres."""
        user = User.objects.create_user(
            username='johndoe',
            password='pass123'
        )
        assert user.get_full_name() == 'johndoe'

    def test_user_str_representation(self):
        """Test: Representación en string del usuario."""
        user = User.objects.create_user(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='pass123',
            role=User.UserRole.STUDENT
        )
        expected = 'Test User (Estudiante)'
        assert str(user) == expected

    def test_user_role_properties(self):
        """Test: Propiedades de verificación de rol."""
        student = User.objects.create_user(
            username='student',
            password='pass123',
            role=User.UserRole.STUDENT
        )
        teacher = User.objects.create_user(
            username='teacher',
            password='pass123',
            role=User.UserRole.TEACHER
        )

        assert student.is_student
        assert not student.is_teacher
        assert teacher.is_teacher
        assert not teacher.is_student


@pytest.mark.django_db
class TestProfileModel:
    """Tests para el modelo Profile."""

    def test_create_profile(self):
        """Test: Crear perfil asociado a usuario."""
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'bio': 'Test bio',
                'city': 'Pasto',
                'country': 'Colombia',
            }
        )
        if not created:
            profile.bio = 'Test bio'
            profile.city = 'Pasto'
            profile.country = 'Colombia'
            profile.save()
        assert profile.user == user
        assert profile.bio == 'Test bio'
        assert profile.city == 'Pasto'
        assert profile.is_active

    def test_profile_str_representation(self):
        """Test: Representación en string del perfil."""
        user = User.objects.create_user(
            username='john',
            first_name='John',
            last_name='Doe',
            password='pass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        assert str(profile) == 'Perfil de John Doe'

    def test_profile_one_to_one_relationship(self):
        """Test: Relación uno a uno entre User y Profile."""
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)

        # Acceso desde user a profile
        assert user.profile == profile
        # Acceso desde profile a user
        assert profile.user == user

    def test_profile_soft_delete(self):
        """Test: Eliminación lógica del perfil."""
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)

        assert profile.is_active
        profile.soft_delete()
        profile.refresh_from_db()
        assert not profile.is_active

    def test_profile_restore(self):
        """Test: Restauración de perfil eliminado lógicamente."""
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)

        profile.soft_delete()
        assert not profile.is_active

        profile.restore()
        profile.refresh_from_db()
        assert profile.is_active
