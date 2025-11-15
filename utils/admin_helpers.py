"""
Utilidades para el panel administrativo.
Funciones reutilizables para vistas, validaciones y helpers.
"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator para requerir que el usuario sea administrador.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('users:login')
        
        if request.user.role != 'admin':
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def paginate_queryset(queryset, request, per_page=20):
    """
    Paginador reutilizable para querysets.
    
    Args:
        queryset: QuerySet a paginar
        request: HttpRequest object
        per_page: Items por página (default: 20)
    
    Returns:
        Page object
    """
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj


def build_search_query(search_term, fields):
    """
    Construir query Q para búsqueda en múltiples campos.
    
    Args:
        search_term: Término a buscar
        fields: Lista de nombres de campos
    
    Returns:
        Q object
    """
    if not search_term:
        return Q()
    
    query = Q()
    for field in fields:
        query |= Q(**{f"{field}__icontains": search_term})
    
    return query


def get_query_string(request, exclude=None):
    """
    Construir query string preservando parámetros actuales.
    
    Args:
        request: HttpRequest object
        exclude: Lista de parámetros a excluir
    
    Returns:
        String con query params
    """
    if exclude is None:
        exclude = ['page']
    
    params = request.GET.copy()
    for param in exclude:
        params.pop(param, None)
    
    if params:
        return '&' + params.urlencode()
    return ''


def get_role_badge_class(role):
    """
    Obtener clase CSS para badge según rol.
    
    Args:
        role: String con el rol del usuario
    
    Returns:
        String con clase CSS
    """
    badges = {
        'admin': 'bg-danger',
        'teacher': 'bg-success',
        'student': 'bg-primary',
    }
    return badges.get(role, 'bg-secondary')


def get_role_display(role):
    """
    Obtener nombre legible del rol.
    
    Args:
        role: String con el rol del usuario
    
    Returns:
        String con nombre del rol
    """
    roles = {
        'admin': 'Administrador',
        'teacher': 'Profesor',
        'student': 'Estudiante',
    }
    return roles.get(role, role)


def validate_form_errors(form):
    """
    Extraer errores del formulario en formato legible.
    
    Args:
        form: Form object
    
    Returns:
        Lista de strings con errores
    """
    errors = []
    
    if form.non_field_errors():
        errors.extend(form.non_field_errors())
    
    for field, field_errors in form.errors.items():
        if field != '__all__':
            errors.append(f"{form.fields[field].label}: {', '.join(field_errors)}")
    
    return errors
