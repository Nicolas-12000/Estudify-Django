from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel
from apps.users.models import User
from apps.core.validators import validate_code_field, validate_text_field, validate_alphanumeric_with_spaces


class Course(AbstractBaseModel):
	name = models.CharField(_('Nombre'), max_length=255)
	code = models.CharField(_('Código'), max_length=50)
	description = models.TextField(_('Descripción'), blank=True)
	academic_year = models.IntegerField(_('Año académico'))
	semester = models.IntegerField(_('Semestre'))
	teacher = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name='courses_taught',
		limit_choices_to={'role': User.UserRole.TEACHER},
		verbose_name=_('Docente')
	)
	max_students = models.PositiveIntegerField(_('Máximo estudiantes'), default=30)

	class Meta:
		verbose_name = _('Curso')
		verbose_name_plural = _('Cursos')
		unique_together = [['code', 'academic_year', 'semester']]

	def __str__(self):
		return f"{self.name} ({self.academic_year}-{self.semester})"

	@property
	def enrolled_count(self):
		return self.enrollments.filter(is_active=True).count()

	@property
	def is_full(self):
		if not self.max_students:
			return False
		return self.enrolled_count >= self.max_students
	
	def clean(self):
		"""Validación personalizada de campos."""
		super().clean()
		if self.name:
			validate_alphanumeric_with_spaces(self.name)
		if self.code:
			validate_code_field(self.code)
		if self.description:
			validate_text_field(self.description)


class Subject(AbstractBaseModel):
	name = models.CharField(_('Nombre'), max_length=255)
	code = models.CharField(_('Código'), max_length=50, unique=True)
	description = models.TextField(_('Descripción'), blank=True)
	credits = models.PositiveSmallIntegerField(_('Créditos'), default=0)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
	teacher = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name='subjects_taught',
		limit_choices_to={'role': User.UserRole.TEACHER},
	)

	class Meta:
		verbose_name = _('Materia')
		verbose_name_plural = _('Materias')

	def __str__(self):
		return f"{self.name} - {self.course.name}"
	
	def clean(self):
		"""Validación personalizada de campos."""
		super().clean()
		if self.name:
			validate_alphanumeric_with_spaces(self.name)
		if self.code:
			validate_code_field(self.code)
		if self.description:
			validate_text_field(self.description)


class CourseEnrollment(AbstractBaseModel):
	student = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='enrollments',
		limit_choices_to={'role': User.UserRole.STUDENT},
	)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

	class Meta:
		verbose_name = _('Inscripción')
		verbose_name_plural = _('Inscripciones')
		unique_together = [['student', 'course']]

	def __str__(self):
		return f"{self.student.get_full_name()} - {self.course.name}"


__all__ = ['Course', 'Subject', 'CourseEnrollment']

