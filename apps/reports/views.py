from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

from apps.academics.models import Attendance, Grade
from utils.reports import ExcelReportGenerator, PDFReportGenerator
from django.shortcuts import get_object_or_404
from apps.users.models import User
from django.db.models import Q
import logging
from django.contrib import messages
from django.shortcuts import redirect

@login_required
def report_list(request):
    """
    Vista para mostrar la lista de reportes disponibles.
    Opcional: muestra solo a usuarios autenticados.
    """
    # Provide context for filters: courses for teachers/admins
    courses = []
    if request.user.is_authenticated:
        if getattr(request.user, 'is_admin_role', False) or request.user.is_superuser:
            from apps.courses.models import Course
            courses = Course.objects.all().order_by('name')
        elif getattr(request.user, 'is_teacher', False):
            from apps.courses.models import Course
            courses = Course.objects.filter(teacher=request.user).order_by('name')

    # also provide students list so UI can offer boletín por estudiante
    students = []
    if request.user.is_authenticated:
        if getattr(request.user, 'is_admin_role', False) or request.user.is_superuser:
            students = User.objects.filter(role=User.UserRole.STUDENT, is_active=True).order_by('last_name', 'first_name')
        elif getattr(request.user, 'is_teacher', False):
            # students enrolled in teacher's courses
            from apps.courses.models import Course
            courses_qs = Course.objects.filter(teacher=request.user)
            students = User.objects.filter(enrollments__course__in=courses_qs, role=User.UserRole.STUDENT, is_active=True).distinct().order_by('last_name', 'first_name')

    return render(request, 'reports/report_list.html', {
        'courses': courses,
        'students': students,
    })


@login_required
def export_attendance_excel(request):
    """Exportar asistencias a Excel.

    - Docentes: exportan asistencias de sus cursos.
    - Admin: exporta todo.
    Parámetros GET opcionales: `show_inactive=1` para incluir estudiantes inactivos.
    """
    if getattr(request.user, 'is_admin_role', False):
        attendances = Attendance.objects.all()
    elif getattr(request.user, 'is_teacher', False):
        attendances = Attendance.objects.filter(course__teacher=request.user)
    else:
        raise PermissionDenied

    if not request.GET.get('show_inactive') == '1':
        attendances = attendances.filter(student__is_active=True)

    try:
        return ExcelReportGenerator.generate_attendance_excel(attendances)
    except Exception as e:
        logging.exception('Failed to generate attendance Excel')
        messages.error(request, 'Error generando reporte de asistencias: ' + str(e))
        return redirect('reports:report_list')


@login_required
def export_grades_excel(request):
    """Exportar calificaciones a Excel.

    - Docentes: exportan sus materias.
    - Admin: exporta todo.
    """
    if getattr(request.user, 'is_admin_role', False):
        grades = Grade.objects.all()
    elif getattr(request.user, 'is_teacher', False):
        grades = Grade.objects.filter(subject__teacher=request.user)
    else:
        raise PermissionDenied

    # support optional filters: ?course_id=XX&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    course_id = request.GET.get('course_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if course_id:
        grades = grades.filter(subject__course_id=course_id)
    if start_date:
        grades = grades.filter(graded_date__gte=start_date)
    if end_date:
        grades = grades.filter(graded_date__lte=end_date)

    try:
        return ExcelReportGenerator.generate_grades_excel(grades)
    except Exception as e:
        logging.exception('Failed to generate grades Excel')
        messages.error(request, 'Error generando reporte de calificaciones: ' + str(e))
        return redirect('reports:report_list')


@login_required
def download_boletin_pdf(request, student_id):
    """Descargar boletín PDF de un estudiante (admin o docente).

    - Admin puede descargar cualquier boletín.
    - Docente sólo puede descargar boletines de estudiantes inscritos en sus cursos.
    """
    student = get_object_or_404(User, pk=student_id, role=User.UserRole.STUDENT)

    # permiso
    if not (getattr(request.user, 'is_admin_role', False) or getattr(request.user, 'is_teacher', False)):
        raise PermissionDenied

    # Si es docente, verificar que el estudiante esté inscrito en alguna de sus materias
    if getattr(request.user, 'is_teacher', False) and not request.user.is_superuser:
        enrolled = student.enrollments.filter(course__teacher=request.user, is_active=True).exists()
        if not enrolled:
            raise PermissionDenied

    grades_qs = Grade.objects.filter(student=student)
    course_id = request.GET.get('course_id')
    if course_id:
        grades_qs = grades_qs.filter(subject__course_id=course_id)

    try:
        return PDFReportGenerator.generate_grade_report(student, grades_qs, course=None)
    except Exception as e:
        logging.exception('Failed to generate boletin PDF for student %s', student_id)
        messages.error(request, 'Error generando boletín PDF: ' + str(e))
        return redirect('reports:report_list')
