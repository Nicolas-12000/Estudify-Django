"""
Permisos personalizados para la API REST de Estudify.
Define qué acciones puede realizar cada rol (admin, teacher, student).
"""
from rest_framework import permissions


# Helper predicates to reduce duplicated role checks
def _is_authenticated(request):
    return bool(getattr(request, "user", None) and request.user.is_authenticated)


def _is_staff(user):
    return bool(getattr(user, "is_staff", False))


def _is_admin(user):
    return _is_staff(user) or bool(getattr(user, "is_admin_role", False))


def _is_teacher(user):
    return bool(getattr(user, "is_teacher", False))


def _is_student(user):
    return bool(getattr(user, "is_student", False))


def _has_full_access(user):
    return _is_admin(user) or _is_teacher(user)


class IsAdminUser(permissions.BasePermission):
    """Solo usuarios con rol admin o staff pueden acceder."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (_is_authenticated(request) and _is_admin(request.user))
        )


class IsTeacherOrAdmin(permissions.BasePermission):
    """Solo profesores o admins pueden acceder."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (_is_authenticated(request) and (_is_admin(request.user) or _is_teacher(request.user)))
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
        if not _is_authenticated(request):
            return False

        # Admin y profesores tienen acceso completo
        if _has_full_access(request.user):
            return True

        # Estudiantes solo pueden listar/ver (GET)
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admin y profesores pueden todo
        if _has_full_access(request.user):
            return True

        # Estudiantes solo pueden VER sus propias calificaciones
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return obj.student == request.user

        return False


class AttendancePermission(permissions.BasePermission):
    """
    Permisos para asistencia:
    - Admins y profesores pueden crear/editar/eliminar
    - Estudiantes solo pueden ver SU propia asistencia
    """

    def has_permission(self, request, view):
        if not _is_authenticated(request):
            return False

        # Admin y profesores tienen acceso completo
        if _has_full_access(request.user):
            return True

        # Estudiantes solo pueden listar/ver (GET)
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admin y profesores pueden todo
        if _has_full_access(request.user):
            return True

        # Estudiantes solo pueden VER su propia asistencia
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
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
        if not _is_authenticated(request):
            return False

        # Admin tiene acceso completo
        if _is_admin(request.user):
            return True

        # Profesores pueden ver e inscribir estudiantes en sus cursos
        if _is_teacher(request.user):
            return True

        # Estudiantes solo pueden ver (GET)
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if _is_admin(request.user):
            return True

        # Profesores pueden gestionar inscripciones de sus cursos
        if _is_teacher(request.user):
            return obj.course.teacher == request.user

        # Estudiantes solo pueden ver sus propias inscripciones
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
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
        if not _is_authenticated(request):
            return False

        # Admin tiene acceso completo
        if _is_admin(request.user):
            return True

        # Profesores pueden ver todos y crear
        if _is_teacher(request.user):
            return True

        # Estudiantes solo pueden listar/ver (GET)
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if _is_admin(request.user):
            return True

        # Profesores pueden editar solo sus cursos
        if _is_teacher(request.user):
            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.teacher == request.user

        # Estudiantes solo pueden ver cursos donde están inscritos
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return obj.enrollments.filter(
                student=request.user, is_active=True
            ).exists()

        return False


class SubjectPermission(permissions.BasePermission):
    """
    Permisos para materias:
    - Admins pueden crear/editar/eliminar
    - Profesores pueden ver todas, editar solo las suyas
    - Estudiantes solo pueden ver materias de cursos donde están inscritos
    """

    def has_permission(self, request, view):
        if not _is_authenticated(request):
            return False

        # Admin tiene acceso completo
        if _is_admin(request.user):
            return True

        # Profesores pueden ver todas y crear
        if _is_teacher(request.user):
            return True

        # Estudiantes solo pueden listar/ver (GET)
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if _is_admin(request.user):
            return True

        # Profesores pueden editar solo sus materias
        if _is_teacher(request.user):
            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.teacher == request.user

        # Estudiantes solo pueden ver materias de cursos inscritos
        if _is_student(request.user) and request.method in permissions.SAFE_METHODS:
            return obj.course.enrollments.filter(
                student=request.user,
                is_active=True,
            ).exists()

        return False
