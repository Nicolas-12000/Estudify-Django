from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Avg, Count
from .forms import GradeImportForm, GradeForm, AttendanceForm, BulkAttendanceForm
from apps.academics.models import Grade, Attendance
from apps.courses.models import Subject, Course, CourseEnrollment
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
    """Listado de calificaciones filtrable por docente/estudiante."""
    qs = Grade.objects.select_related('student', 'subject', 'subject__course')
    if getattr(request.user, 'is_teacher', False):
        qs = qs.filter(subject__teacher=request.user)
    elif getattr(request.user, 'is_student', False):
        qs = qs.filter(student=request.user)
    return render(request, 'academics/grades_list.html', {'grades': qs})

@login_required
def attendance_list(request):
    """Listado de asistencias filtrable por docente/estudiante/curso."""
    qs = Attendance.objects.select_related('student', 'course')
    if getattr(request.user, 'is_teacher', False):
        qs = qs.filter(course__teacher=request.user)
    elif getattr(request.user, 'is_student', False):
        qs = qs.filter(student=request.user)
    return render(request, 'academics/attendance_list.html', {'attendances': qs})

# ----- VISTAS DE CREACIÓN -----
@login_required
def grade_create(request):
    """Crear nueva calificación."""
    if request.method == 'POST':
        form = GradeForm(request.POST, teacher=request.user)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.graded_by = request.user if getattr(request.user, 'is_teacher', False) else None
            grade.save()
            return redirect('academics:grades_list')
    else:
        form = GradeForm(teacher=request.user)
    return render(request, 'academics/grade_form.html', {'form': form})

@login_required
def attendance_create(request):
    """Crear nueva asistencia unitaria y registro masivo opcional por curso."""
    if request.method == 'POST':
        form = AttendanceForm(request.POST, teacher=request.user)
        bulk_form = BulkAttendanceForm(request.POST, teacher=request.user)
        if 'save_single' in request.POST and form.is_valid():
            form.save()
            return redirect('academics:attendance_list')
        elif 'save_bulk' in request.POST and bulk_form.is_valid():
            course = bulk_form.cleaned_data['course']
            date = bulk_form.cleaned_data['date']
            # Construir formset para cada estudiante inscrito (presente por defecto)
            enrolled = CourseEnrollment.objects.filter(course=course, is_active=True).select_related('student')
            with transaction.atomic():
                for e in enrolled:
                    Attendance.objects.get_or_create(
                        student=e.student,
                        course=course,
                        date=date,
                        defaults={'status': Attendance.AttendanceStatus.PRESENT, 'recorded_by': request.user}
                    )
            return redirect('academics:attendance_list')
    else:
        form = AttendanceForm(teacher=request.user)
        bulk_form = BulkAttendanceForm(teacher=request.user)
    return render(request, 'academics/attendance_form.html', {'form': form, 'bulk_form': bulk_form})


# ----- DASHBOARD Y APIs -----
@login_required
def dashboard_view(request):
    courses = Course.objects.filter(is_active=True)
    subjects = Subject.objects.filter(is_active=True)
    return render(request, 'academics/dashboard.html', {
        'courses': courses,
        'subjects': subjects,
    })

@login_required
def api_grades_average(request):
    """Retorna promedio de calificaciones por materia o curso."""
    subject_id = request.GET.get('subject')
    course_id = request.GET.get('course')

    qs = Grade.objects.all()
    if getattr(request.user, 'is_teacher', False):
        qs = qs.filter(subject__teacher=request.user)
    elif getattr(request.user, 'is_student', False):
        qs = qs.filter(student=request.user)

    label = "Promedio general"
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
        subject = Subject.objects.filter(pk=subject_id).first()
        label = f"Promedio - {subject.name}" if subject else label
    elif course_id:
        qs = qs.filter(subject__course_id=course_id)
        course = Course.objects.filter(pk=course_id).first()
        label = f"Promedio - {course.name}" if course else label

    avg = qs.aggregate(avg=Avg('value'))['avg'] or 0
    data = {
        'labels': [label],
        'datasets': [
            {'label': 'Promedio', 'data': [round(float(avg), 2)]}
        ]
    }
    return JsonResponse(data)

@login_required
def api_attendance_monthly(request):
    """Retorna asistencia mensual por curso en el año indicado."""
    course_id = request.GET.get('course')
    year = request.GET.get('year')

    if not course_id:
        return JsonResponse({'error': 'course requerido'}, status=400)

    qs = Attendance.objects.filter(course_id=course_id)
    if year:
        qs = qs.filter(date__year=year)

    if getattr(request.user, 'is_teacher', False):
        qs = qs.filter(course__teacher=request.user)
    elif getattr(request.user, 'is_student', False):
        qs = qs.filter(student=request.user)

    # Agrupar por mes y estado
    from django.db.models.functions import ExtractMonth
    agg = (
        qs.annotate(month=ExtractMonth('date'))
          .values('month', 'status')
          .annotate(count=Count('id'))
          .order_by('month', 'status')
    )

    # Construir estructura para Chart.js (labels 1..12)
    labels = [1,2,3,4,5,6,7,8,9,10,11,12]
    status_map = {k: [0]*12 for k in ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']}
    for row in agg:
        m = int(row['month']) if row['month'] else None
        if m:
            idx = m - 1
            status_map[row['status']][idx] = row['count']

    data = {
        'labels': labels,
        'datasets': [
            {'label': 'Presentes', 'data': status_map['PRESENT']},
            {'label': 'Ausentes', 'data': status_map['ABSENT']},
            {'label': 'Tarde', 'data': status_map['LATE']},
            {'label': 'Excusado', 'data': status_map['EXCUSED']},
        ]
    }
    return JsonResponse(data)
