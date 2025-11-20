from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from apps.users.forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from apps.users.models import User, Profile
from apps.courses.models import Subject
from django.db.models import Q
from django.core.exceptions import PermissionDenied

def is_admin(user):
    return user.is_authenticated and (getattr(user, "is_admin_role", False) or user.is_staff)

def is_teacher(user):
    return user.is_authenticated and getattr(user, "role", None) == User.UserRole.TEACHER

def is_student(user):
    return user.is_authenticated and getattr(user, "role", None) == User.UserRole.STUDENT

def home(request):
    return render(request, "home.html", {})

@login_required
def panel_admin(request):
    if not is_admin(request.user):
        raise PermissionDenied
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

@login_required
def panel_profesor(request):
    if not is_teacher(request.user):
        raise PermissionDenied
    subjects = Subject.objects.filter(teacher=request.user)
    subjects_count = subjects.count()
    students_count = sum(sub.students.count() for sub in subjects)
    return render(request, "core/panel_profesor.html", {
        'subjects': subjects,
        'subjects_count': subjects_count,
        'students_count': students_count,
    })

@login_required
def panel_estudiante(request):
    if not is_student(request.user):
        raise PermissionDenied
    courses = getattr(request.user.profile, 'courses', [])
    courses_count = len(courses) if hasattr(courses, '__len__') else courses.count() if hasattr(courses, 'count') else 0
    grades_summary = "—"
    return render(request, "core/panel_estudiante.html", {
        'courses': courses,
        'courses_count': courses_count,
        'grades_summary': grades_summary,
    })

@login_required
def register_view(request):
    if not is_admin(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect('users:user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        # Redirige según rol aunque ya haya sesión
        if is_admin(request.user):
            return redirect('panel_admin')
        elif is_teacher(request.user):
            return redirect('panel_profesor')
        elif is_student(request.user):
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
                messages.success(request, f'Bienvenido, {user.get_full_name()}!')
                if is_admin(user):
                    return redirect('panel_admin')
                elif is_teacher(user):
                    return redirect('panel_profesor')
                elif is_student(user):
                    return redirect('panel_estudiante')
                else:
                    return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('users:login')

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    subjects = Subject.objects.filter(teacher=request.user, is_active=True) if is_teacher(request.user) else None
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
    if not is_admin(request.user):
        raise PermissionDenied
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
    user = get_object_or_404(User, pk=pk)
    if not (is_admin(request.user) or request.user == user):
        raise PermissionDenied
    return render(request, 'users/user_detail.html', {'user_obj': user})

@login_required
def toggle_user_status(request, pk):
    if not is_admin(request.user):
        raise PermissionDenied
    user = get_object_or_404(User, pk=pk)
    if user.is_active:
        user.is_active = False
        messages.warning(request, f'Usuario {user.username} desactivado.')
    else:
        user.is_active = True
        messages.success(request, f'Usuario {user.username} activado.')
    user.save()
    return redirect('users:user_list')
