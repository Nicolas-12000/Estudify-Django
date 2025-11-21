from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from apps.users.forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from apps.users.models import User, Profile
from apps.courses.models import Subject
from django.db.models import Q

def is_admin(user):
    return user.is_authenticated and (user.is_admin_role or user.is_staff)

# ---------- HOME VIEW (página principal genérica) ----------
def home(request):
    """Renderiza el home general (HOME.html) con formulario de login embebido.

    Pasamos una instancia de `UserLoginForm` y el parámetro `next` (si existe)
    para que la plantilla pueda centralizar el inicio de sesión y preservar
    parámetros GET existentes al redirigir.
    """
    form = UserLoginForm(request)
    next_param = request.GET.get('next', '')
    return render(request, "HOME.html", {
        'form': form,
        'next_param': next_param,
    })

# ---------- PANEL ADMINISTRADOR (redirigido desde login si es staff/admin/superuser) ----------
@login_required
def panel_admin(request):
    total_users = User.objects.count()
    total_teachers = User.objects.filter(role=User.UserRole.TEACHER).count()
    total_students = User.objects.filter(role=User.UserRole.STUDENT).count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    return render(request, "core/panel_admin.html", {
        'total_users': total_users,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'recent_users': recent_users,
    })

# ---------- PANEL PROFESOR ----------
@login_required
def panel_profesor(request):
    subjects = Subject.objects.filter(teacher=request.user)
    subjects_count = subjects.count()
    students_count = sum(sub.students.count() for sub in subjects)
    return render(request, "core/panel_profesor.html", {
        'subjects': subjects,
        'subjects_count': subjects_count,
        'students_count': students_count,
    })

# ---------- PANEL ESTUDIANTE ----------
@login_required
def panel_estudiante(request):
    courses = getattr(request.user.profile, 'courses', [])  # ajusta si usas FK/M2M
    courses_count = len(courses) if hasattr(courses, '__len__') else courses.count() if hasattr(courses, 'count') else 0
    grades_summary = "—"
    return render(request, "core/panel_estudiante.html", {
        'courses': courses,
        'courses_count': courses_count,
        'grades_summary': grades_summary,
    })

def register_view(request):
    """
    Vista pública para registrar nuevos usuarios desde la landing.
    Campos: nombre, correo, contraseña, confirmar contraseña y rol (docente/estudiante).
    Genera un username automático y crea el perfil.
    """
    from apps.users.forms import PublicUserRegistrationForm

    if request.method == 'POST':
        form = PublicUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear perfil por si las señales no lo manejan inmediatamente
            try:
                Profile.objects.get_or_create(user=user)
            except Exception:
                pass
            messages.success(request, "Registro completado. Puedes iniciar sesión ahora.")
            return redirect('users:login')
    else:
        form = PublicUserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

# ----------- LOGIN CON REDIRECCIÓN A PANEL SEGÚN ROL -----------
def login_view(request):
    """
    Vista para inicio de sesión.
    """
    if request.user.is_authenticated:
        # Redirige según rol aunque ya haya sesión
        if request.user.is_admin_role or request.user.is_staff:
            return redirect('panel_admin')
        elif request.user.role == User.UserRole.TEACHER:
            return redirect('panel_profesor')
        elif request.user.role == User.UserRole.STUDENT:
            return redirect('panel_estudiante')
        else:
            return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is None and username and '@' in username:
                try:
                    user_obj = User.objects.get(email__iexact=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_full_name()}!!')
                
                if user.is_superuser or user.is_staff or getattr(user, "is_admin_role", False):
                    return redirect('panel_admin')

    

        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    """
    Vista para cerrar sesión.
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('users:login')

@login_required
def profile_view(request):
    """
    Ver y editar perfil de usuario.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    subjects = Subject.objects.filter(teacher=request.user, is_active=True) if getattr(request.user, 'is_teacher', False) else None

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'users/profile.html', {
        'form': form,
        'profile': profile,
        'subjects': subjects,
    })

@login_required
def user_list_view(request):
    """
    Vista para listar usuarios (solo admin/staff).
    """
    if not request.user.is_admin_role and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')

    users = User.objects.all().order_by('-date_joined')
    role_filter = request.GET.get('role')
    search = request.GET.get('search')

    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    return render(request, 'users/user_list.html', {
        'users': users,
        'role_choices': User.UserRole.choices
    })

@login_required
def user_detail_view(request, pk):
    """
    Detalle de usuario.
    """
    user = get_object_or_404(User, pk=pk)
    if not (request.user.is_admin_role or request.user.is_staff or request.user == user):
        messages.error(request, 'No tienes permisos para ver este perfil.')
        return redirect('home')
    return render(request, 'users/user_detail.html', {'user_obj': user})

@login_required
def toggle_user_status(request, pk):
    """
    Activar/desactivar usuario (solo admin/staff).
    """
    if not (request.user.is_admin_role or request.user.is_staff):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('home')
    user = get_object_or_404(User, pk=pk)
    if user.is_active:
        user.is_active = False
        messages.warning(request, f'Usuario {user.username} desactivado.')
    else:
        user.is_active = True
        messages.success(request, f'Usuario {user.username} activado.')
    user.save()
    return redirect('users:user_loging')
