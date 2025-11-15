from django import template
from urllib.parse import urlencode

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary."""
    if dictionary:
        return dictionary.get(key, '')
    return ''


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Build query string preserving existing params."""
    request = context['request']
    query_dict = request.GET.copy()
    
    for key, value in kwargs.items():
        if value:
            query_dict[key] = value
        elif key in query_dict:
            del query_dict[key]
    
    if query_dict:
        return '&' + urlencode(query_dict)
    return ''


@register.inclusion_tag('admin_panel/components/badge_role.html')
def badge_role(role):
    """Render badge for user role."""
    badge_classes = {
        'admin': 'bg-danger',
        'teacher': 'bg-success',
        'student': 'bg-primary',
    }
    
    role_names = {
        'admin': 'Administrador',
        'teacher': 'Profesor',
        'student': 'Estudiante',
    }
    
    return {
        'role': role,
        'badge_class': badge_classes.get(role, 'bg-secondary'),
        'role_name': role_names.get(role, role),
    }


@register.inclusion_tag('admin_panel/components/badge_status.html')
def badge_status(is_active):
    """Render badge for active/inactive status."""
    return {
        'is_active': is_active,
        'badge_class': 'bg-success' if is_active else 'bg-secondary',
        'status_text': 'Activo' if is_active else 'Inactivo',
    }


@register.filter
def percentage(value, total):
    """Calculate percentage."""
    if total == 0:
        return 0
    return round((value / total) * 100)


@register.filter
def add_class(field, css_class):
    """Add CSS class to form field."""
    return field.as_widget(attrs={"class": css_class})
