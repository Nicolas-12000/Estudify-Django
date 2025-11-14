from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from apps.core.models import AbstractBaseModel
from apps.users.models import User
from apps.courses.models import Subject, Course


class Grade(AbstractBaseModel):
	"""
	Modelo para representar las calificaciones de los estudiantes.
	Escala: 0.0 a 5.0 (sistema colombiano)
	"""
	student = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='grades',
		limit_choices_to={'role': User.UserRole.STUDENT},
		verbose_name=_('Estudiante'),
		help_text=_('Estudiante calificado')
	)
	subject = models.ForeignKey(
		Subject,
		on_delete=models.CASCADE,
		related_name='grades',
		verbose_name=_('Materia'),
		help_text=_('Materia calificada')
	)
	value = models.DecimalField(
		_('Calificación'),
		max_digits=3,
		decimal_places=1,
		validators=[
			MinValueValidator(0.0),
			MaxValueValidator(5.0)
		],
		help_text=_('Valor de la calificación (0.0 - 5.0)')
	)
	grade_type = models.CharField(
		_('Tipo de calificación'),
		max_length=50,
		choices=[
			('QUIZ', _('Quiz')),
			('EXAM', _('Examen')),
			('HOMEWORK', _('Tarea')),
			('PROJECT', _('Proyecto')),
			('PARTICIPATION', _('Participación')),
			('FINAL', _('Final')),
		],
		default='EXAM',
		help_text=_('Tipo de evaluación')
	)
	weight = models.DecimalField(
		_('Peso'),
		max_digits=5,
		decimal_places=2,
		default=100.00,
		validators=[
			MinValueValidator(0.0),
			MaxValueValidator(100.0)
		],
		help_text=_('Peso porcentual de la calificación')
	)
	comments = models.TextField(
		_('Comentarios'),
		blank=True,
		help_text=_('Comentarios del docente sobre la calificación')
	)
	graded_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name='grades_given',
		limit_choices_to={'role': User.UserRole.TEACHER},
		verbose_name=_('Calificado por'),
		help_text=_('Docente que asignó la calificación')
	)
	graded_date = models.DateField(
		_('Fecha de calificación'),
		auto_now_add=True,
		help_text=_('Fecha en que se asignó la calificación')
	)

	class Meta:
		verbose_name = _('Calificación')
		verbose_name_plural = _('Calificaciones')
		ordering = ['-graded_date']
		indexes = [
			models.Index(fields=['student', 'subject']),
			models.Index(fields=['graded_date']),
		]

	def __str__(self):
		return f"{self.student.get_full_name()} - {self.subject.name}: {self.value}"

	def clean(self):
		"""Validación personalizada para verificar que el estudiante esté inscrito en el curso."""
		if self.student and self.subject:
			from apps.courses.models import CourseEnrollment
			if not CourseEnrollment.objects.filter(
				student=self.student,
				course=self.subject.course,
				is_active=True
			).exists():
				raise ValidationError(
					_('El estudiante no está inscrito en el curso de esta materia.')
				)

	@property
	def is_passing(self):
		"""Verifica si la calificación es aprobatoria (>= 3.0)."""
		return self.value >= 3.0

	@property
	def letter_grade(self):
		"""Retorna la calificación en formato letra."""
		try:
			value = float(self.value)
		except (TypeError, ValueError):
			return ''
		if value >= 4.5:
			return 'A'
		elif value >= 4.0:
			return 'B'
		elif value >= 3.0:
			return 'C'
		elif value >= 2.0:
			return 'D'
		else:
			return 'F'


class Attendance(AbstractBaseModel):
	"""
	Modelo para registrar la asistencia de estudiantes.
	"""
	class AttendanceStatus(models.TextChoices):
		PRESENT = 'PRESENT', _('Presente')
		ABSENT = 'ABSENT', _('Ausente')
		LATE = 'LATE', _('Tarde')
		EXCUSED = 'EXCUSED', _('Excusado')

	student = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='attendances',
		limit_choices_to={'role': User.UserRole.STUDENT},
		verbose_name=_('Estudiante'),
		help_text=_('Estudiante del registro de asistencia')
	)
	course = models.ForeignKey(
		Course,
		on_delete=models.CASCADE,
		related_name='attendances',
		verbose_name=_('Curso'),
		help_text=_('Curso del registro')
	)
	date = models.DateField(
		_('Fecha'),
		help_text=_('Fecha de la asistencia')
	)
	status = models.CharField(
		_('Estado'),
		max_length=10,
		choices=AttendanceStatus.choices,
		default=AttendanceStatus.PRESENT,
		help_text=_('Estado de asistencia')
	)
	notes = models.TextField(
		_('Notas'),
		blank=True,
		help_text=_('Notas adicionales sobre la asistencia')
	)
	recorded_by = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		related_name='attendances_recorded',
		limit_choices_to={'role': User.UserRole.TEACHER},
		verbose_name=_('Registrado por'),
		help_text=_('Docente que registró la asistencia')
	)

	class Meta:
		verbose_name = _('Asistencia')
		verbose_name_plural = _('Asistencias')
		unique_together = [['student', 'course', 'date']]
		ordering = ['-date']
		indexes = [
			models.Index(fields=['student', 'date']),
			models.Index(fields=['course', 'date']),
		]

	def __str__(self):
		return f"{self.student.get_full_name()} - {self.course.name} ({self.date}): {self.get_status_display()}"

	def clean(self):
		"""Validación para verificar que el estudiante esté inscrito en el curso."""
		if self.student and self.course:
			from apps.courses.models import CourseEnrollment
			if not CourseEnrollment.objects.filter(
				student=self.student,
				course=self.course,
				is_active=True
			).exists():
				raise ValidationError(
					_('El estudiante no está inscrito en este curso.')
				)


__all__ = ['Grade', 'Attendance']
