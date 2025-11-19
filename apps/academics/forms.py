"""
Formularios para gestión académica en Estudify.
Incluye forms para Grade y Attendance.
"""

from django import forms

from apps.academics.models import Attendance, Grade
from apps.courses.models import Course, Subject
from apps.users.models import User


class GradeForm(forms.ModelForm):
    """
    Formulario para crear/editar calificaciones.
    """

    class Meta:
        model = Grade
        fields = [
            'student',
            'subject',
            'value',
            'grade_type',
            'weight',
            'comments']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '5'
            }),
            'grade_type': forms.Select(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        # Permitir pasar el docente actual para filtrar
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        # Filtrar solo estudiantes
        self.fields['student'].queryset = User.objects.filter(
            role=User.UserRole.STUDENT,
            is_active=True
        )

        # Si hay un docente, filtrar materias que imparte
        if teacher and teacher.is_teacher:
            self.fields['subject'].queryset = Subject.objects.filter(
                teacher=teacher,
                is_active=True
            )

    def clean(self):
        """Validación personalizada."""
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        subject = cleaned_data.get('subject')

        if student and subject:
            # Verificar que el estudiante esté inscrito en el curso
            from apps.courses.models import CourseEnrollment
            if not CourseEnrollment.objects.filter(
                student=student,
                course=subject.course,
                is_active=True
            ).exists():
                raise forms.ValidationError(
                    'El estudiante no está inscrito en el curso de esta materia.'
                )

        return cleaned_data


class AttendanceForm(forms.ModelForm):
    """
    Formulario para registrar asistencia.
    """

    class Meta:
        model = Attendance
        fields = ['student', 'course', 'date', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        # Filtrar solo estudiantes
        self.fields['student'].queryset = User.objects.filter(
            role=User.UserRole.STUDENT,
            is_active=True
        )

        # Si hay docente, filtrar cursos que imparte
        if teacher and teacher.is_teacher:
            self.fields['course'].queryset = Course.objects.filter(
                teacher=teacher,
                is_active=True
            )

    def clean(self):
        """Validación personalizada."""
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')

        if student and course:
            # Verificar que el estudiante esté inscrito en el curso
            from apps.courses.models import CourseEnrollment
            if not CourseEnrollment.objects.filter(
                student=student,
                course=course,
                is_active=True
            ).exists():
                raise forms.ValidationError(
                    'El estudiante no está inscrito en este curso.'
                )

        return cleaned_data


class BulkAttendanceForm(forms.Form):
    """
    Formulario para registrar asistencia masiva de un curso.
    """
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Curso'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha'
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        # Filtrar cursos del docente
        if teacher and teacher.is_teacher:
            self.fields['course'].queryset = Course.objects.filter(
                teacher=teacher,
                is_active=True
            )


# ... (todo tu código anterior queda igual)

class GradeFilterForm(forms.Form):
    """
    Formulario para filtrar calificaciones en reportes.
    """
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Curso'
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Materia'
    )
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role=User.UserRole.STUDENT,
            is_active=True
        ),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Estudiante'
    )
    grade_type = forms.ChoiceField(
        choices=[('', 'Todos')] + list(Grade._meta.get_field('grade_type').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo'
    )

class GradeImportForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.UserRole.STUDENT, is_active=True),
        required=True,
        label='Estudiante',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    file = forms.FileField(
        label='Archivo de notas (Excel .xlsx)',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
