"""
Vistas administrativas para Estudify.
Panel de administración completo para gestión de usuarios, cursos, materias, etc.
Solo accesible por usuarios con rol admin.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.courses.forms import CourseEnrollmentForm, CourseForm, SubjectForm
from apps.courses.models import Course, CourseEnrollment, Subject
from apps.users.forms import UserRegistrationForm
from apps.users.models import Profile, User


def is_admin(user):
    """Verificar que el usuario sea admin o staff."""
    return user.is_authenticated and (user.is_staff or user.is_admin_role)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Dashboard principal del administrador.
    Muestra estadísticas generales del sistema.
    """
    context = {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role=User.UserRole.STUDENT).count(),
        'total_teachers': User.objects.filter(role=User.UserRole.TEACHER).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_subjects': Subject.objects.filter(is_active=True).count(),
        'total_enrollments': CourseEnrollment.objects.filter(is_active=True).count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_courses': Course.objects.order_by('-created_at')[:5],
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ==================== GESTIÓN DE USUARIOS ====================

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """Listar todos los usuarios con filtros y búsqueda."""
    users = User.objects.all().select_related('profile').order_by('-date_joined')

    # Filtros
    role = request.GET.get('role')
    search = request.GET.get('search')
    is_active = request.GET.get('is_active')

    if role:
        users = users.filter(role=role)
    if is_active:
        users = users.filter(is_active=is_active == 'true')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Paginación
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)

    context = {
        'users': users,
        'role_choices': User.UserRole.choices,
        'current_role': role,
        'current_search': search or '',
    }
    return render(request, 'admin_panel/user_list.html', context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Crear nuevo usuario."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear perfil automáticamente
            Profile.objects.get_or_create(user=user)
            messages.success(
                request, f'Usuario {
                    user.username} creado exitosamente.')
            return redirect('admin_panel:user_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'admin_panel/user_form.html',
                  {'form': form, 'action': 'Crear'})


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Editar usuario existente."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # Actualizar campos básicos
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.role = request.POST.get('role', user.role)
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()

        messages.success(
            request, f'Usuario {
                user.username} actualizado exitosamente.')
        return redirect('admin_panel:user_list')

    return render(request, 'admin_panel/user_edit.html', {'user_obj': user})


@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    """Eliminar (desactivar) usuario."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.warning(request, f'Usuario {user.username} desactivado.')
        return redirect('admin_panel:user_list')

    return render(request,
                  'admin_panel/user_confirm_delete.html',
                  {'user_obj': user})


# ==================== GESTIÓN DE CURSOS ====================

@login_required
@user_passes_test(is_admin)
def course_list(request):
    """Listar todos los cursos."""
    courses = Course.objects.all().select_related('teacher').annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-academic_year', 'semester', 'name')

    # Filtros
    academic_year = request.GET.get('academic_year')
    semester = request.GET.get('semester')
    teacher = request.GET.get('teacher')
    search = request.GET.get('search')

    if academic_year:
        courses = courses.filter(academic_year=academic_year)
    if semester:
        courses = courses.filter(semester=semester)
    if teacher:
        courses = courses.filter(teacher_id=teacher)
    if search:
        courses = courses.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )

    # Paginación
    paginator = Paginator(courses, 15)
    page = request.GET.get('page')
    courses = paginator.get_page(page)

    context = {
        'courses': courses,
        'teachers': User.objects.filter(role=User.UserRole.TEACHER),
        'current_search': search or '',
    }
    return render(request, 'admin_panel/course_list.html', context)


@login_required
@user_passes_test(is_admin)
def course_create(request):
    """Crear nuevo curso."""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f'Curso {
                    course.name} creado exitosamente.')
            return redirect('admin_panel:course_list')
    else:
        form = CourseForm()

    return render(request, 'admin_panel/course_form.html',
                  {'form': form, 'action': 'Crear'})


@login_required
@user_passes_test(is_admin)
def course_edit(request, pk):
    """Editar curso existente."""
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Curso {
                    course.name} actualizado exitosamente.')
            return redirect('admin_panel:course_list')
    else:
        form = CourseForm(instance=course)

    return render(request, 'admin_panel/course_form.html',
                  {'form': form, 'action': 'Editar', 'course': course})


@login_required
@user_passes_test(is_admin)
def course_delete(request, pk):
    """Eliminar (desactivar) curso."""
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        course.is_active = False
        course.save()
        messages.warning(request, f'Curso {course.name} desactivado.')
        return redirect('admin_panel:course_list')

    return render(request,
                  'admin_panel/course_confirm_delete.html',
                  {'course': course})


@login_required
@user_passes_test(is_admin)
def course_detail(request, pk):
    """Ver detalle de curso con estudiantes inscritos."""
    course = get_object_or_404(Course, pk=pk)
    enrollments = course.enrollments.filter(
        is_active=True).select_related('student')
    subjects = course.subjects.filter(is_active=True)

    context = {
        'course': course,
        'enrollments': enrollments,
        'subjects': subjects,
    }
    return render(request, 'admin_panel/course_detail.html', context)


# ==================== GESTIÓN DE MATERIAS ====================

@login_required
@user_passes_test(is_admin)
def subject_list(request):
    """Listar todas las materias."""
    subjects = Subject.objects.all().select_related(
        'course', 'teacher').order_by('course', 'name')

    # Filtros
    course_id = request.GET.get('course')
    teacher_id = request.GET.get('teacher')
    search = request.GET.get('search')

    if course_id:
        subjects = subjects.filter(course_id=course_id)
    if teacher_id:
        subjects = subjects.filter(teacher_id=teacher_id)
    if search:
        subjects = subjects.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )

    # Paginación
    paginator = Paginator(subjects, 15)
    page = request.GET.get('page')
    subjects = paginator.get_page(page)

    context = {
        'subjects': subjects,
        'courses': Course.objects.filter(is_active=True),
        'teachers': User.objects.filter(role=User.UserRole.TEACHER),
        'current_search': search or '',
    }
    return render(request, 'admin_panel/subject_list.html', context)


@login_required
@user_passes_test(is_admin)
def subject_create(request):
    """Crear nueva materia."""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(
                request, f'Materia {
                    subject.name} creada exitosamente.')
            return redirect('admin_panel:subject_list')
    else:
        form = SubjectForm()

    return render(request, 'admin_panel/subject_form.html',
                  {'form': form, 'action': 'Crear'})


@login_required
@user_passes_test(is_admin)
def subject_edit(request, pk):
    """Editar materia existente."""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Materia {
                    subject.name} actualizada exitosamente.')
            return redirect('admin_panel:subject_list')
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'admin_panel/subject_form.html',
                  {'form': form, 'action': 'Editar', 'subject': subject})


@login_required
@user_passes_test(is_admin)
def subject_delete(request, pk):
    """Eliminar (desactivar) materia."""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        subject.is_active = False
        subject.save()
        messages.warning(request, f'Materia {subject.name} desactivada.')
        return redirect('admin_panel:subject_list')

    return render(request,
                  'admin_panel/subject_confirm_delete.html',
                  {'subject': subject})


# ==================== GESTIÓN DE INSCRIPCIONES ====================

@login_required
@user_passes_test(is_admin)
def enrollment_list(request):
    """Listar todas las inscripciones."""
    enrollments = CourseEnrollment.objects.all().select_related(
        'student', 'course'
    ).order_by('-created_at')

    # Filtros
    course_id = request.GET.get('course')
    student_id = request.GET.get('student')

    if course_id:
        enrollments = enrollments.filter(course_id=course_id)
    if student_id:
        enrollments = enrollments.filter(student_id=student_id)

    # Paginación
    paginator = Paginator(enrollments, 20)
    page = request.GET.get('page')
    enrollments = paginator.get_page(page)

    context = {
        'enrollments': enrollments,
        'courses': Course.objects.filter(is_active=True),
        'students': User.objects.filter(role=User.UserRole.STUDENT),
    }
    return render(request, 'admin_panel/enrollment_list.html', context)


@login_required
@user_passes_test(is_admin)
def enrollment_create(request):
    """Crear nueva inscripción."""
    if request.method == 'POST':
        form = CourseEnrollmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscripción creada exitosamente.')
            return redirect('admin_panel:enrollment_list')
    else:
        form = CourseEnrollmentForm()

    return render(request, 'admin_panel/enrollment_form.html',
                  {'form': form, 'action': 'Crear'})


@login_required
@user_passes_test(is_admin)
def enrollment_delete(request, pk):
    """Eliminar (desactivar) inscripción."""
    enrollment = get_object_or_404(CourseEnrollment, pk=pk)

    if request.method == 'POST':
        enrollment.is_active = False
        enrollment.save()
        messages.warning(request, 'Inscripción desactivada.')
        return redirect('admin_panel:enrollment_list')

    return render(request,
                  'admin_panel/enrollment_confirm_delete.html',
                  {'enrollment': enrollment})
