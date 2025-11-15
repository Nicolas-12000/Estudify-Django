"""
Permisos personalizados para la API REST de Estudify.
Define qué acciones puede realizar cada rol (admin, teacher, student).
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Solo usuarios con rol admin o staff pueden acceder."""
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and (request.user.is_staff or request.user.is_admin_role)
        )


class IsTeacherOrAdmin(permissions.BasePermission):
    """Solo profesores o admins pueden acceder."""
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and (
                request.user.is_staff 
                or request.user.is_admin_role 
                or request.user.is_teacher
            )
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso para que solo el dueño pueda editar.
    Otros pueden leer.
    """
    
    def has_object_permission(self, request, view, obj):
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para el dueño
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'student'):
            return obj.student == request.user
        
        return False


class GradePermission(permissions.BasePermission):
    """
    Permisos para calificaciones:
    - Admins y profesores pueden crear/editar/eliminar
    - Estudiantes solo pueden ver SUS propias calificaciones
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y profesores tienen acceso completo
        if request.user.is_staff or request.user.is_admin_role or request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden listar/ver (GET)
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin y profesores pueden todo
        if request.user.is_staff or request.user.is_admin_role or request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden VER sus propias calificaciones
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return obj.student == request.user
        
        return False


class AttendancePermission(permissions.BasePermission):
    """
    Permisos para asistencia:
    - Admins y profesores pueden crear/editar/eliminar
    - Estudiantes solo pueden ver SU propia asistencia
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y profesores tienen acceso completo
        if request.user.is_staff or request.user.is_admin_role or request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden listar/ver (GET)
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin y profesores pueden todo
        if request.user.is_staff or request.user.is_admin_role or request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden VER su propia asistencia
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return obj.student == request.user
        
        return False


class CourseEnrollmentPermission(permissions.BasePermission):
    """
    Permisos para inscripciones:
    - Admins pueden todo
    - Profesores pueden ver inscripciones de sus cursos
    - Estudiantes solo pueden ver SUS propias inscripciones
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin tiene acceso completo
        if request.user.is_staff or request.user.is_admin_role:
            return True
        
        # Profesores pueden ver e inscribir estudiantes en sus cursos
        if request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden ver (GET)
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.is_staff or request.user.is_admin_role:
            return True
        
        # Profesores pueden gestionar inscripciones de sus cursos
        if request.user.is_teacher:
            return obj.course.teacher == request.user
        
        # Estudiantes solo pueden ver sus propias inscripciones
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return obj.student == request.user
        
        return False


class CoursePermission(permissions.BasePermission):
    """
    Permisos para cursos:
    - Admins pueden crear/editar/eliminar
    - Profesores pueden ver todos, editar solo los suyos
    - Estudiantes solo pueden ver cursos donde están inscritos
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin tiene acceso completo
        if request.user.is_staff or request.user.is_admin_role:
            return True
        
        # Profesores pueden ver todos y crear
        if request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden listar/ver (GET)
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.is_staff or request.user.is_admin_role:
            return True
        
        # Profesores pueden editar solo sus cursos
        if request.user.is_teacher:
            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.teacher == request.user
        
        # Estudiantes solo pueden ver cursos donde están inscritos
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return obj.enrollments.filter(student=request.user, is_active=True).exists()
        
        return False


class SubjectPermission(permissions.BasePermission):
    """
    Permisos para materias:
    - Admins pueden crear/editar/eliminar
    - Profesores pueden ver todas, editar solo las suyas
    - Estudiantes solo pueden ver materias de cursos donde están inscritos
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin tiene acceso completo
        if request.user.is_staff or request.user.is_admin_role:
            return True
        
        # Profesores pueden ver todas y crear
        if request.user.is_teacher:
            return True
        
        # Estudiantes solo pueden listar/ver (GET)
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.is_staff or request.user.is_admin_role:
            return True
        
        # Profesores pueden editar solo sus materias
        if request.user.is_teacher:
            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.teacher == request.user
        
        # Estudiantes solo pueden ver materias de cursos inscritos
        if request.user.is_student and request.method in permissions.SAFE_METHODS:
            return obj.course.enrollments.filter(
                student=request.user, 
                is_active=True
            ).exists()
        
        return False
