from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from apps.core.models import AbstractBaseModel
from apps.core.validators import (
    validate_name_field,
    validate_username_field,
    validate_text_field,
    validate_alphanumeric_with_spaces,
)

class User(AbstractUser):
	"""
	Usuario personalizado con roles diferenciados.
	Roles: ADMIN, TEACHER (Docente), STUDENT (Estudiante)
	"""
	class UserRole(models.TextChoices):
		ADMIN = 'ADMIN', _('Administrador')
		TEACHER = 'TEACHER', _('Docente')
		STUDENT = 'STUDENT', _('Estudiante')

	role = models.CharField(
		_('Rol'),
		max_length=10,
		choices=UserRole.choices,
		default=UserRole.STUDENT,
		help_text=_('Rol del usuario en el sistema')
	)
	phone = models.CharField(
		_('Teléfono'),
		max_length=15,
		blank=True,
		null=True,
		help_text=_('Número de teléfono de contacto')
	)
	
	def clean(self):
		"""Validación personalizada de campos."""
		super().clean()
		if self.first_name:
			validate_name_field(self.first_name)
		if self.last_name:
			validate_name_field(self.last_name)
		if self.username:
			validate_username_field(self.username)
	avatar = models.ImageField(
		_('Avatar'),
		upload_to='avatars/',
		blank=True,
		null=True,
		help_text=_('Imagen de perfil del usuario')
	)
	date_of_birth = models.DateField(
		_('Fecha de nacimiento'),
		blank=True,
		null=True,
		help_text=_('Fecha de nacimiento del usuario')
	)

	groups = models.ManyToManyField(
		Group,
		verbose_name=_('groups'),
		blank=True,
		help_text=_('The groups this user belongs to.'),
		related_name='custom_user_set',
		related_query_name='custom_user',
	)
	user_permissions = models.ManyToManyField(
		Permission,
		verbose_name=_('user permissions'),
		blank=True,
		help_text=_('Specific permissions for this user.'),
		related_name='custom_user_set',
		related_query_name='custom_user',
	)

	class Meta:
		verbose_name = _('Usuario')
		verbose_name_plural = _('Usuarios')
		ordering = ['last_name', 'first_name']
		indexes = [
			models.Index(fields=['email']),
			models.Index(fields=['role']),
		]

	def __str__(self):
		return f"{self.get_full_name()} ({self.get_role_display()})"

	def get_full_name(self):
		"""Retorna el nombre completo del usuario."""
		full_name = f"{self.first_name} {self.last_name}".strip()
		return full_name or self.username

	@property
	def is_teacher(self):
		"""Verifica si el usuario es docente."""
		return self.role == self.UserRole.TEACHER

	@property
	def is_student(self):
		"""Verifica si el usuario es estudiante."""
		return self.role == self.UserRole.STUDENT

	@property
	def is_admin_role(self):
		"""Verifica si el usuario es administrador."""
		return self.role == self.UserRole.ADMIN


class Profile(AbstractBaseModel):
	"""
	Perfil extendido del usuario con información adicional.
	"""
	user = models.OneToOneField(
		User,
		on_delete=models.CASCADE,
		related_name='profile',
		verbose_name=_('Usuario')
	)
	bio = models.TextField(
		_('Biografía'),
		blank=True,
		help_text=_('Biografía o descripción del usuario')
	)
	address = models.CharField(
		_('Dirección'),
		max_length=255,
		blank=True,
		help_text=_('Dirección de residencia')
	)
	city = models.CharField(
		_('Ciudad'),
		max_length=100,
		blank=True,
		help_text=_('Ciudad de residencia')
	)
	country = models.CharField(
		_('País'),
		max_length=100,
		default='Colombia',
		help_text=_('País de residencia')
	)
	
	def clean(self):
		"""Validación personalizada de campos."""
		super().clean()
		if self.bio:
			validate_text_field(self.bio)
		if self.address:
			validate_alphanumeric_with_spaces(self.address)
		if self.city:
			validate_alphanumeric_with_spaces(self.city)
		if self.country:
			validate_alphanumeric_with_spaces(self.country)

	class Meta:
		verbose_name = _('Perfil')
		verbose_name_plural = _('Perfiles')

	def __str__(self):
		return f"Perfil de {self.user.get_full_name()}"


__all__ = ['User', 'Profile']

