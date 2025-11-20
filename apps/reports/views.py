from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from apps.academics.models import Grade, Attendance
from apps.courses.models import Course, Subject
from apps.users.models import User


@login_required
def report_list(request):
    return render(request, 'reports/report_list.html', {})


@login_required
def student_report(request, student_id):
    """Boletín HTML del estudiante (exportable a PDF con WeasyPrint si se desea)."""
    student = get_object_or_404(User, pk=student_id)
    # Obtener cursos y materias donde tiene calificaciones
    grades = Grade.objects.filter(student=student).select_related('subject', 'subject__course')
    subjects = Subject.objects.filter(grades__student=student).distinct()

    # Promedio por materia
    avg_by_subject = (
        grades.values('subject__id', 'subject__name')
        .annotate(avg=Avg('value'), count=Count('id'))
        .order_by('subject__name')
    )

    # Asistencia por curso
    attendance = Attendance.objects.filter(student=student)
    attendance_summary = (
        attendance.values('course__id', 'course__name', 'status')
        .annotate(count=Count('id'))
        .order_by('course__name', 'status')
    )

    return render(request, 'reports/boletin.html', {
        'student': student,
        'grades': grades,
        'avg_by_subject': avg_by_subject,
        'attendance_summary': attendance_summary,
        'generated_at': timezone.now(),
    })


@login_required
def course_acta(request, course_id, subject_id=None):
    """Acta HTML del curso (y opcionalmente por materia)."""
    course = get_object_or_404(Course, pk=course_id)
    subject = None
    if subject_id:
        subject = get_object_or_404(Subject, pk=subject_id, course=course)

    grades = Grade.objects.filter(subject__course=course)
    if subject:
        grades = grades.filter(subject=subject)

    # Promedios por estudiante
    avg_by_student = (
        grades.values('student__id', 'student__first_name', 'student__last_name', 'student__username')
        .annotate(avg=Avg('value'), count=Count('id'))
        .order_by('student__last_name', 'student__first_name')
    )

    return render(request, 'reports/acta.html', {
        'course': course,
        'subject': subject,
        'avg_by_student': avg_by_student,
        'generated_at': timezone.now(),
    })
