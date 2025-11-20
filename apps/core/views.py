from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from apps.users.models import User

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
    # Puedes agregar aquí métricas, recent_users, etc.
    return render(request, "core/panel_admin.html")

@login_required
def panel_profesor(request):
    user = request.user
    if not user.is_teacher:
        raise PermissionDenied
    return render(request, "core/panel_profesor.html")

@login_required
def panel_estudiante(request):
    user = request.user
    if not user.is_student:
        raise PermissionDenied
    return render(request, "core/panel_estudiante.html")
