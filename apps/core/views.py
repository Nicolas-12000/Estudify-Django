from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    """
    Renderiza la página principal usando la plantilla base (HOME.html).
    """
    return render(request, "HOME.html", {})

@login_required
def panel_admin(request):
    """
    Panel exclusivo para usuarios Administradores.
    """
    return render(request, 'core/panel_admin.html')

@login_required
def panel_profesor(request):
    """
    Panel exclusivo para usuarios Profesores.
    """
    return render(request, 'core/panel_profesor.html')

@login_required
def panel_estudiante(request):
    """
    Panel exclusivo para usuarios Estudiantes.
    """
    return render(request, 'core/panel_estudiante.html')
