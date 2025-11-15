"""
Constantes y configuraciones reutilizables para el proyecto.
"""

# Paginación
PAGINATION_PER_PAGE = {
    'users': 20,
    'courses': 15,
    'subjects': 15,
    'enrollments': 20,
    'grades': 25,
    'attendance': 30,
}

# Roles de usuario
USER_ROLES = {
    'admin': 'Administrador',
    'teacher': 'Profesor',
    'student': 'Estudiante',
}

# Badges CSS por rol
ROLE_BADGE_CLASSES = {
    'admin': 'bg-danger',
    'teacher': 'bg-success',
    'student': 'bg-primary',
}

# Estados
STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'

STATUS_CHOICES = [
    (STATUS_ACTIVE, 'Activo'),
    (STATUS_INACTIVE, 'Inactivo'),
]

# Configuración de año académico
CURRENT_ACADEMIC_YEAR = 2025
ACADEMIC_YEAR_RANGE = range(2020, 2031)  # 2020-2030

# Semestres
SEMESTER_CHOICES = [
    (1, 'Primer Semestre'),
    (2, 'Segundo Semestre'),
]

# Mensajes del sistema
MESSAGES = {
    'success': {
        'user_created': 'Usuario creado exitosamente.',
        'user_updated': 'Usuario actualizado exitosamente.',
        'user_deleted': 'Usuario eliminado exitosamente.',
        'course_created': 'Curso creado exitosamente.',
        'course_updated': 'Curso actualizado exitosamente.',
        'course_deleted': 'Curso eliminado exitosamente.',
        'subject_created': 'Materia creada exitosamente.',
        'subject_updated': 'Materia actualizada exitosamente.',
        'subject_deleted': 'Materia eliminada exitosamente.',
        'enrollment_created': 'Inscripción realizada exitosamente.',
        'enrollment_deleted': 'Inscripción eliminada exitosamente.',
    },
    'error': {
        'permission_denied': 'No tienes permisos para realizar esta acción.',
        'not_authenticated': 'Debes iniciar sesión para acceder.',
        'invalid_form': 'Por favor corrige los errores del formulario.',
        'duplicate_entry': 'Ya existe un registro con estos datos.',
        'max_capacity': 'El curso ha alcanzado su capacidad máxima.',
    },
    'warning': {
        'no_results': 'No se encontraron resultados.',
        'course_full': 'El curso está lleno.',
        'already_enrolled': 'El estudiante ya está inscrito en este curso.',
    },
}

# Configuración de búsqueda
SEARCH_FIELDS = {
    'users': ['username', 'email', 'first_name', 'last_name'],
    'courses': ['code', 'name', 'description'],
    'subjects': ['name', 'description'],
}

# Formato de fechas
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'

# Iconos Font Awesome por sección
SECTION_ICONS = {
    'dashboard': 'tachometer-alt',
    'users': 'users',
    'courses': 'book',
    'subjects': 'graduation-cap',
    'enrollments': 'user-graduate',
    'grades': 'star',
    'attendance': 'calendar-check',
    'reports': 'chart-bar',
    'settings': 'cog',
}
