"""
Formularios para gestión de cursos, materias e inscripciones.
"""
from django import forms
from apps.courses.models import Course, Subject, CourseEnrollment
from apps.users.models import User


class CourseForm(forms.ModelForm):
    """Formulario para crear/editar cursos."""
    
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'academic_year', 'semester', 'teacher', 'max_students', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del curso'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción'}),
            'academic_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2025'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1 o 2'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(role=User.UserRole.TEACHER)
        self.fields['teacher'].empty_label = "Seleccionar profesor..."


class SubjectForm(forms.ModelForm):
    """Formulario para crear/editar materias."""
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'credits', 'course', 'teacher', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la materia'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Créditos'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        self.fields['teacher'].queryset = User.objects.filter(role=User.UserRole.TEACHER)
        self.fields['course'].empty_label = "Seleccionar curso..."
        self.fields['teacher'].empty_label = "Seleccionar profesor..."


class CourseEnrollmentForm(forms.ModelForm):
    """Formulario para crear inscripciones."""
    
    class Meta:
        model = CourseEnrollment
        fields = ['student', 'course', 'is_active']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(role=User.UserRole.STUDENT)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        self.fields['student'].empty_label = "Seleccionar estudiante..."
        self.fields['course'].empty_label = "Seleccionar curso..."
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        
        if student and course:
            # Verificar si ya existe inscripción activa
            if CourseEnrollment.objects.filter(
                student=student,
                course=course,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError('El estudiante ya está inscrito en este curso.')
            
            # Verificar capacidad del curso
            if course.is_full:
                raise forms.ValidationError('El curso ha alcanzado su capacidad máxima.')
        
        return cleaned_data
