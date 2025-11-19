from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import GradeImportForm
from apps.academics.models import Grade
from apps.courses.models import Subject
import pandas as pd

# ----- IMPORTACIÓN DE NOTAS DESDE EXCEL -----
@login_required
def import_grades(request):
    """Importar calificaciones en masa desde archivo Excel. Solo profesores."""
    if not getattr(request.user, 'is_teacher', False):
        return redirect('home')

    if request.method == 'POST':
        form = GradeImportForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.cleaned_data['student']
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)
            except Exception:
                form.add_error('file', 'Archivo no válido o formato incorrecto (.xlsx esperado)')
                return render(request, 'academics/import_grades.html', {'form': form})

            errores = []
            successful = 0
            for i, row in df.iterrows():
                subject_code = str(row.get('materia_codigo', '')).strip()
                valor = row.get('valor', None)
                if not subject_code or pd.isnull(valor):
                    continue  # Saltar filas sin datos

                try:
                    value = float(valor)
                    grade_type = str(row.get('tipo', '')).strip()
                    weight = float(row.get('peso', 100.0))
                    comments = str(row.get('comentario', ''))
                    subject = Subject.objects.get(code=subject_code, teacher=request.user)
                    Grade.objects.create(
                        student=student,
                        subject=subject,
                        value=value,
                        grade_type=grade_type,
                        weight=weight,
                        comments=comments,
                        graded_by=request.user
                    )
                    successful += 1
                except Exception as e:
                    errores.append(f"Fila {i+2}: {str(e)}")
            return render(request, 'academics/import_result.html', {
                'errors': errores,
                'success_count': successful
            })
    else:
        form = GradeImportForm()
    return render(request, 'academics/import_grades.html', {'form': form})

# ----- VISTAS DE LISTADO -----
@login_required
def grades_list(request):
    """
    Listado de calificaciones (puedes filtrar por usuario/rol aquí).
    """
    # Puedes pasar una lista de calificaciones si lo deseas
    # grades = Grade.objects.all()
    return render(request, 'academics/grades_list.html')#, {'grades': grades})

@login_required
def attendance_list(request):
    """
    Listado de asistencias.
    """
    # attendances = Attendance.objects.all()
    return render(request, 'academics/attendance_list.html')#, {'attendances': attendances})

# ----- VISTAS DE CREACIÓN -----
@login_required
def grade_create(request):
    """
    Crear nueva calificación (formulario).
    """
    return render(request, 'academics/grade_form.html')

@login_required
def attendance_create(request):
    """
    Crear nueva asistencia (formulario).
    """
    return render(request, 'academics/attendance_form.html')
