from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AbstractBaseModel
from apps.core.validators import (validate_alphanumeric_with_spaces,
                                  validate_code_field, validate_text_field)
from apps.users.models import User


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
    max_students = models.PositiveIntegerField(
        _('Máximo estudiantes'), default=30)
    # legacy fields `classroom` and `schedule` removed in favor of CourseSession/TimeSlot

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
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subjects')
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
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments')

    class Meta:
        verbose_name = _('Inscripción')
        verbose_name_plural = _('Inscripciones')
        unique_together = [['student', 'course']]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.name}"


class TimeSlot(AbstractBaseModel):
    """Representa una franja horaria recurrente semanalmente."""
    MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
    DAY_CHOICES = [
        (MON, 'Lunes'), (TUE, 'Martes'), (WED, 'Miércoles'),
        (THU, 'Jueves'), (FRI, 'Viernes'), (SAT, 'Sábado'), (SUN, 'Domingo'),
    ]

    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = 'Franja horaria'
        verbose_name_plural = 'Franjas horarias'
        unique_together = [['day_of_week', 'start_time', 'end_time']]

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Classroom(AbstractBaseModel):
    name = models.CharField('Nombre', max_length=100)
    location = models.CharField('Ubicación', max_length=255, blank=True)
    capacity = models.PositiveIntegerField('Capacidad', null=True, blank=True)

    class Meta:
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'

    def __str__(self):
        return self.name


class CourseSession(AbstractBaseModel):
    """Instancia recurrente de clase asociada a un curso.

    Se utiliza como la fuente de verdad para horarios de curso, profesores y estudiantes.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name='sessions')
    classroom_fk = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name='sessions')
    recurrence = models.CharField('Recurrencia', max_length=50, blank=True, help_text='p.ej. weekly')
    notes = models.TextField('Notas', blank=True)

    class Meta:
        verbose_name = 'Sesión de curso'
        verbose_name_plural = 'Sesiones de curso'
        indexes = [models.Index(fields=['course', 'timeslot'])]

    def __str__(self):
        return f"{self.course.name} - {self.timeslot}"

    def clean(self):
        """Validaciones para evitar solapamientos de aula y de docente."""
        from django.core.exceptions import ValidationError

        # obtener información de la franja actual
        if not self.timeslot:
            return
        day = self.timeslot.day_of_week
        start = self.timeslot.start_time
        end = self.timeslot.end_time

        # chequeo por aula (existe otro session con mismo día cuyo timeslot se solapa)
        if self.classroom_fk:
            conflict_qs = CourseSession.objects.filter(
                classroom_fk=self.classroom_fk,
                timeslot__day_of_week=day,
                timeslot__start_time__lt=end,
                timeslot__end_time__gt=start,
                is_active=True,
            )
            if self.pk:
                conflict_qs = conflict_qs.exclude(pk=self.pk)
            if conflict_qs.exists():
                raise ValidationError('Solapamiento detectado: la aula ya está ocupada en esa franja.')

        # chequeo por docente
        teacher = None
        if self.course and self.course.teacher_id:
            teacher = self.course.teacher
        if teacher:
            conflict_qs = CourseSession.objects.filter(
                course__teacher=teacher,
                timeslot__day_of_week=day,
                timeslot__start_time__lt=end,
                timeslot__end_time__gt=start,
                is_active=True,
            )
            if self.pk:
                conflict_qs = conflict_qs.exclude(pk=self.pk)
            if conflict_qs.exists():
                raise ValidationError('Solapamiento detectado: el docente tiene otra clase en esa franja.')


__all__ = ['Course', 'Subject', 'CourseEnrollment', 'TimeSlot', 'Classroom', 'CourseSession']
