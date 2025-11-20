from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import GradeImportForm, GradeForm, AttendanceForm, BulkAttendanceForm
from apps.academics.models import Grade, Attendance
from apps.courses.models import Subject
import pandas as pd
from django.core.exceptions import PermissionDenied
from apps.courses.models import Course
from apps.courses.models import CourseEnrollment
from apps.users.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q
import calendar
from django.shortcuts import get_object_or_404
from django.contrib import messages
from apps.users.forms import UserRegistrationForm, UserProfileForm
from apps.users.models import Profile
import json

# ---- IMPORTACIÓN DE NOTAS DESDE EXCEL ----
@login_required
def import_grades(request):
    """Importar calificaciones desde archivo Excel (.xlsx) — SOLO docentes."""
    if not getattr(request.user, 'is_teacher', False):
        return redirect('home')

    if request.method == 'POST':
        # Two-step import: preview then confirm
        form = GradeImportForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.cleaned_data['student']
            # confirmation step
            if request.POST.get('confirm') == '1':
                preview_key = f'import_preview_{request.user.id}'
                preview = request.session.get(preview_key, [])
                errores = []
                exitosos = 0
                for idx, row in enumerate(preview):
                    if not row.get('valid'):
                        errores.append(f"Fila {idx+2}: {row.get('error')}")
                        continue
                    try:
                        subject = Subject.objects.get(code=row['materia_codigo'], teacher=request.user)
                        Grade.objects.create(
                            student=student,
                            subject=subject,
                            value=row['valor'],
                            grade_type=row.get('tipo', '') or 'EXAM',
                            weight=row.get('peso', 100.0),
                            comments=row.get('comentario', ''),
                            graded_by=request.user
                        )
                        exitosos += 1
                    except Exception as e:
                        errores.append(f"Fila {idx+2}: {str(e)}")

                # cleanup
                try:
                    del request.session[preview_key]
                except Exception:
                    pass

                return render(request, 'academics/import_result.html', {
                    'errors': errores,
                    'success_count': exitosos
                })

            # first step: parse and prepare preview
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)
            except Exception:
                form.add_error('file', 'Archivo no válido o formato incorrecto (.xlsx esperado)')
                return render(request, 'academics/import_grades.html', {'form': form})

            preview = []
            for i, row in df.iterrows():
                subject_code = str(row.get('materia_codigo', '')).strip()
                valor = row.get('valor', None)
                entry = {
                    'materia_codigo': subject_code,
                    'valor': None,
                    'tipo': str(row.get('tipo', '')).strip(),
                    'peso': float(row.get('peso', 100.0)) if not pd.isnull(row.get('peso', None)) else 100.0,
                    'comentario': str(row.get('comentario', '') or ''),
                    'valid': True,
                    'error': None,
                }
                # basic validation
                if not subject_code:
                    entry['valid'] = False
                    entry['error'] = 'Código de materia vacío'
                elif pd.isnull(valor):
                    entry['valid'] = False
                    entry['error'] = 'Valor de la nota vacío'
                else:
                    try:
                        entry['valor'] = float(valor)
                    except Exception:
                        entry['valid'] = False
                        entry['error'] = f'Valor no numérico: {valor}'

                # check subject ownership and enrollment
                if entry['valid']:
                    try:
                        subj = Subject.objects.get(code=subject_code, teacher=request.user)
                    except Subject.DoesNotExist:
                        entry['valid'] = False
                        entry['error'] = 'Materia no encontrada o no es tuya'
                preview.append(entry)

            # store preview in session for confirmation
            preview_key = f'import_preview_{request.user.id}'
            # convert to json-serializable (already is)
            request.session[preview_key] = preview
            request.session.modified = True

            return render(request, 'academics/import_preview.html', {
                'student': student,
                'preview': preview,
                'form': form,
            })
    else:
        form = GradeImportForm()
    return render(request, 'academics/import_grades.html', {'form': form})

@login_required
def grades_list(request):
    """Listado de calificaciones"""
    # Permitir docentes, administradores y estudiantes (ver sólo sus propias notas)
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False) or getattr(request.user, 'is_student', False)):
        raise PermissionDenied

    if getattr(request.user, 'is_teacher', False):
        grades = Grade.objects.filter(subject__teacher=request.user).order_by('-graded_date')
    elif getattr(request.user, 'is_student', False):
        grades = Grade.objects.filter(student=request.user).order_by('-graded_date')
    else:
        grades = Grade.objects.all().order_by('-graded_date')

    return render(request, 'academics/grades_list.html', {'grades': grades})

@login_required
def attendance_list(request):
    """Listado de asistencias"""
    # Permitir docentes, administradores y estudiantes (ver sólo su propio historial)
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False) or getattr(request.user, 'is_student', False)):
        raise PermissionDenied

    if getattr(request.user, 'is_teacher', False):
        attendances = Attendance.objects.filter(course__teacher=request.user).order_by('-date')
    elif getattr(request.user, 'is_student', False):
        attendances = Attendance.objects.filter(student=request.user).order_by('-date')
    else:
        attendances = Attendance.objects.all().order_by('-date')

    return render(request, 'academics/attendance_list.html', {'attendances': attendances})

@login_required
def grade_create(request):
    """Crear nueva calificación"""
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False)):
        raise PermissionDenied

    if request.method == 'POST':
        form = GradeForm(request.POST, teacher=request.user)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.graded_by = request.user
            grade.save()
            messages.success(request, 'Calificación creada correctamente.')
            return redirect('academics:grades_list')
    else:
        form = GradeForm(teacher=request.user)

    # Build student options for the template (id, label, username, courses)
    student_options = []
    selected_student_id = None
    try:
        selected_student_id = request.POST.get('student') if request.method == 'POST' else None
        student_qs = form.fields['student'].queryset
        from apps.courses.models import CourseEnrollment
        for s in student_qs.distinct():
            enrolls = CourseEnrollment.objects.filter(student=s, course__teacher=request.user, is_active=True)
            course_ids = [str(e.course_id) for e in enrolls]
            student_options.append({'id': s.id, 'label': s.get_full_name() or s.username, 'username': s.username, 'courses': course_ids})
    except Exception:
        student_options = []

    # Build subject->course map to help client-side filtering
    subject_course_map = {}
    try:
        subj_qs = form.fields['subject'].queryset
        for subj in subj_qs:
            subject_course_map[str(subj.pk)] = str(subj.course_id) if subj.course_id else ''
    except Exception:
        subject_course_map = {}

    subject_course_map_json = json.dumps(subject_course_map)

    return render(request, 'academics/grade_form.html', {
        'form': form,
        'student_options': student_options,
        'selected_student_id': selected_student_id,
        'subject_course_map_json': subject_course_map_json,
    })

@login_required
def attendance_create(request):
    """Crear nueva asistencia"""
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False)):
        raise PermissionDenied

    if request.method == 'POST':
        form = AttendanceForm(request.POST, teacher=request.user)
        if form.is_valid():
            att = form.save(commit=False)
            att.recorded_by = request.user
            att.save()
            messages.success(request, 'Asistencia registrada correctamente.')
            return redirect('academics:attendance_list')
    else:
        form = AttendanceForm(teacher=request.user)

    # Build student -> courses mapping for client-side filtering in template
    student_options = []
    selected_student_id = None
    try:
        # If POST, prefer submitted value so we can pre-select it in the template
        selected_student_id = request.POST.get('student') if request.method == 'POST' else None
        # Use the form's queryset for student field (already filtered by teacher/course)
        student_qs = form.fields['student'].queryset
        # For each student, find their enrolled course ids relevant to this teacher
        from apps.courses.models import CourseEnrollment
        for s in student_qs.distinct():
            enrolls = CourseEnrollment.objects.filter(student=s, course__teacher=request.user, is_active=True)
            course_ids = [str(e.course_id) for e in enrolls]
            student_options.append({'id': s.id, 'label': s.get_full_name() or s.username, 'username': s.username, 'courses': course_ids})
    except Exception:
        student_options = []

    return render(request, 'academics/attendance_form.html', {
        'form': form,
        'student_options': student_options,
        'selected_student_id': selected_student_id,
    })


@login_required
def attendance_bulk(request):
    """Registrar asistencia masiva para un curso (docente/admin)."""
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False)):
        raise PermissionDenied

    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST, teacher=request.user)
        if form.is_valid():
            course = form.cleaned_data['course']
            date = form.cleaned_data['date']
            # students selected via checkboxes
            student_ids = request.POST.getlist('students')
            created = 0
            from apps.courses.models import CourseEnrollment
            for sid in student_ids:
                try:
                    student = User.objects.get(pk=int(sid), role=User.UserRole.STUDENT)
                except Exception:
                    continue
                # Ensure student is enrolled in the course and active
                if not CourseEnrollment.objects.filter(student=student, course=course, is_active=True).exists():
                    continue
                # Create attendance record (default PRESENT)
                Attendance.objects.create(student=student, course=course, date=date, status=Attendance.AttendanceStatus.PRESENT, recorded_by=request.user)
                created += 1

            messages.success(request, f'Asistencias creadas: {created}')
            return redirect('academics:attendance_list')
    else:
        form = BulkAttendanceForm(teacher=request.user)

    # If a course is preselected, list enrolled students
    enrolled_students = []
    try:
        course = form.fields['course'].initial or None
        # if GET with course param, override
        course_id = request.GET.get('course')
        if course_id:
            from apps.courses.models import Course
            course = Course.objects.filter(pk=course_id, teacher=request.user).first()
        if course:
            from apps.courses.models import CourseEnrollment
            enrolls = CourseEnrollment.objects.filter(course=course, is_active=True).select_related('student')
            enrolled_students = [e.student for e in enrolls]
    except Exception:
        enrolled_students = []

    return render(request, 'academics/bulk_attendance_form.html', {
        'form': form,
        'enrolled_students': enrolled_students,
    })


@login_required
def student_list(request):
    """Listado de estudiantes para el docente o admin.

    - Los docentes verán los estudiantes inscritos en sus cursos.
    - Parámetro GET `show_inactive=1` para incluir usuarios inactivos.
    """
    # Permitir sólo docentes y administradores
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False)):
        raise PermissionDenied

    show_inactive = request.GET.get('show_inactive') == '1'

    if getattr(request.user, 'is_admin_role', False):
        students_qs = User.objects.filter(role=User.UserRole.STUDENT)
    else:
        # obtener cursos donde el docente es responsable
        courses = Course.objects.filter(teacher=request.user)
        students_qs = User.objects.filter(enrollments__course__in=courses).distinct()

    if not show_inactive:
        students_qs = students_qs.filter(is_active=True)

    students = students_qs.order_by('last_name', 'first_name')

    return render(request, 'academics/student_list.html', {
        'students': students,
        'show_inactive': show_inactive,
    })


@login_required
def student_create(request):
    """Permite al docente (o admin) crear un estudiante."""
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False)):
        raise PermissionDenied

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Force role to STUDENT regardless of selection
            user.role = User.UserRole.STUDENT
            user.is_active = True
            user.save()
            # ensure profile exists
            Profile.objects.get_or_create(user=user)
            messages.success(request, f'Estudiante {user.get_full_name()} creado correctamente.')
            return redirect('academics:student_list')
    else:
        form = UserRegistrationForm(initial={'role': User.UserRole.STUDENT})

    return render(request, 'academics/student_form.html', {'form': form, 'create': True})


@login_required
def student_edit(request, pk):
    """Permite al docente (o admin) editar la información de un estudiante."""
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False)):
        raise PermissionDenied

    student = get_object_or_404(User, pk=pk, role=User.UserRole.STUDENT)

    # If teacher, ensure student is enrolled in one of their courses
    if getattr(request.user, 'is_teacher', False):
        enrolled = CourseEnrollment.objects.filter(student=student, course__teacher=request.user).exists()
        if not enrolled:
            raise PermissionDenied

    profile, _ = Profile.objects.get_or_create(user=student)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Información de estudiante actualizada.')
            return redirect('academics:student_list')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'academics/student_form.html', {'form': form, 'create': False, 'student': student})


@login_required
def stats_subject_performance(request):
    """Devuelve JSON con promedio de calificaciones por materia para el docente.

    Response: { labels: ["Materia A", ...], data: [3.5, ...] }
    """
    # allow teachers and admins
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False) or request.user.is_superuser):
        return JsonResponse({'error': 'permission_denied'}, status=403)

    if getattr(request.user, 'is_teacher', False):
        subjects = Subject.objects.filter(teacher=request.user)
    else:
        # admin: show all subjects
        subjects = Subject.objects.all()
    labels = []
    data = []
    for s in subjects:
        avg = s.grades.aggregate(avg=Avg('value'))['avg'] or 0
        labels.append(s.name)
        # Convert Decimal to float
        try:
            val = float(avg)
        except Exception:
            val = 0.0
        data.append(round(val, 2))

    return JsonResponse({'labels': labels, 'data': data})


@login_required
def stats_attendance_monthly(request):
    """Devuelve JSON con tasa de asistencia mensual (porcentaje) para el docente.

    Response: { labels: ['Ene','Feb',...], data: [95.0, 88.2, ...] }
    """
    # allow teachers and admins
    if not (getattr(request.user, 'is_teacher', False) or getattr(request.user, 'is_admin_role', False) or request.user.is_superuser):
        return JsonResponse({'error': 'permission_denied'}, status=403)

    year = int(request.GET.get('year', timezone.now().year))
    # Obtener asistencias: si es docente, sólo las de sus cursos; si es admin, todas
    if getattr(request.user, 'is_teacher', False):
        attendances = Attendance.objects.filter(course__teacher=request.user, date__year=year)
    else:
        attendances = Attendance.objects.filter(date__year=year)

    # preparar buckets por mes
    month_labels = [calendar.month_abbr[i] for i in range(1, 13)]
    present_counts = [0] * 12
    total_counts = [0] * 12

    for att in attendances:
        m = att.date.month - 1
        total_counts[m] += 1
        if att.status in (Attendance.AttendanceStatus.PRESENT, Attendance.AttendanceStatus.LATE):
            present_counts[m] += 1

    rates = []
    for i in range(12):
        total = total_counts[i]
        rate = (present_counts[i] / total * 100) if total > 0 else 0.0
        rates.append(round(rate, 1))

    return JsonResponse({'labels': month_labels, 'data': rates})
