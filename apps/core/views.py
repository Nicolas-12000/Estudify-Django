from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from apps.users.models import User
from apps.courses.models import Subject, Course
from apps.courses.models import CourseEnrollment

def home(request):
    """Renderiza la página principal usando la plantilla base (home.html)."""
    return render(request, "home.html", {})

@login_required
def dashboard(request):
    user = request.user
    if user.is_superuser or user.is_staff or user.is_admin_role:
        return redirect('panel_admin')
    elif user.is_teacher:
        return redirect('panel_profesor')
    elif user.is_student:
        return redirect('panel_estudiante')
    else:
        return redirect('logout')

@login_required
def panel_admin(request):
    user = request.user
    if not (user.is_superuser or user.is_staff or user.is_admin_role):
        raise PermissionDenied
    # Métricas para el panel de administrador
    from apps.users.models import User as AppUser
    total_users = AppUser.objects.count()
    total_teachers = AppUser.objects.filter(role=AppUser.UserRole.TEACHER).count()
    total_students = AppUser.objects.filter(role=AppUser.UserRole.STUDENT).count()

    recent_users = AppUser.objects.all().order_by('-date_joined')[:6]

    return render(request, "core/panel_admin.html", {
        'total_users': total_users,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'recent_users': recent_users,
    })

@login_required
def panel_profesor(request):
    user = request.user
    if not user.is_teacher:
        raise PermissionDenied
    # Materias del docente
    subjects = Subject.objects.filter(teacher=user, is_active=True)
    subjects_count = subjects.count()

    # Estudiantes: contar alumnos inscritos en los cursos del docente
    courses = Course.objects.filter(teacher=user, is_active=True)
    students_qs = User.objects.filter(
        enrollments__course__in=courses,
        role=User.UserRole.STUDENT,
        is_active=True
    ).distinct()
    students_count = students_qs.count()

    # Preparar lista de cursos con sus estudiantes inscritos
    course_students = []
    for c in courses:
        enrolled = CourseEnrollment.objects.filter(course=c, is_active=True).select_related('student')
        students = [e.student for e in enrolled]
        course_students.append({'course': c, 'students': students, 'count': len(students)})

    return render(request, "core/panel_profesor.html", {
        'subjects': subjects,
        'subjects_count': subjects_count,
        'students_count': students_count,
        'course_students': course_students,
        'courses': courses,
    })

@login_required
def panel_estudiante(request):
    user = request.user
    if not user.is_student:
        raise PermissionDenied
    # Obtener cursos desde CourseEnrollment
    from apps.courses.models import CourseEnrollment
    enroll_qs = CourseEnrollment.objects.filter(student=user, is_active=True).select_related('course')
    courses = [e.course for e in enroll_qs]
    courses_count = len(courses)

    # Resumen simple de calificaciones
    from apps.academics.models import Grade
    grades_qs = Grade.objects.filter(student=user).order_by('-graded_date')
    recent = grades_qs[:5]
    try:
        from django.db import models as dj_models
        avg = grades_qs.aggregate(avg=dj_models.Avg('value'))['avg']
    except Exception:
        avg = None
    grades_summary = f"Promedio: {round(avg,2)}" if avg is not None else '—'

    return render(request, "core/panel_estudiante.html", {
        'courses': courses,
        'courses_count': courses_count,
        'grades_summary': grades_summary,
        'recent_grades': recent,
    })
