"""
Vistas para gestión de usuarios en Estudify.
Incluye registro, login, logout, perfil y vistas administrativas ligeras.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.users.forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from apps.users.models import User, Profile


def register_view(request):
    """
    Vista para registro de nuevos usuarios.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear perfil automáticamente
            Profile.objects.create(user=user)
            messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """
    Vista para inicio de sesión.
    Credenciales de prueba: admin@estudify.com / Admin123!@#
    """
    if request.user.is_authenticated:
        # Redirigir según rol
        if request.user.is_admin_role or request.user.is_staff:
            return redirect('admin_panel:dashboard')
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Allow login by username OR email
            user = authenticate(username=username, password=password)
            if user is None and username and '@' in username:
                # try to resolve email -> username
                try:
                    user_obj = User.objects.get(email__iexact=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_full_name()}!')
                # Redirigir según rol
                if user.is_admin_role or user.is_staff:
                    return redirect('admin_panel:dashboard')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
    else:
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
    Vista para ver y editar perfil de usuario.
    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    
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
        'profile': profile
    })


@login_required
def user_list_view(request):
    """
    Vista para listar usuarios (solo admin).
    """
    if not request.user.is_admin_role and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Filtros
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
    Vista para ver detalle de un usuario.
    """
    user = get_object_or_404(User, pk=pk)
    
    # Solo admin o el mismo usuario pueden ver el perfil
    if not (request.user.is_admin_role or request.user.is_staff or request.user == user):
        messages.error(request, 'No tienes permisos para ver este perfil.')
        return redirect('home')
    
    return render(request, 'users/user_detail.html', {'user_obj': user})


@login_required
def toggle_user_status(request, pk):
    """
    Vista para activar/desactivar usuario (soft delete).
    Solo admin.
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
    return redirect('users:user_list')
