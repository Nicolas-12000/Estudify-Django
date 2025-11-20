"""
Compatibility re-exports for API viewsets.

Algunos lugares importan desde `apps.api.views`, mientras que las
implementaciones reales viven en `apps.api.v1.viewsets`. Este módulo
re‑exporta las clases ViewSet comunes para que ambos estilos de import
funcionen sin romper nada.

Ejemplos de uso soportados:

    from apps.api.views import UserViewSet
    # o
    from apps.api.v1.viewsets import UserViewSet

Ambos son equivalentes gracias a este archivo.
"""

from apps.api.v1.viewsets import (
    AttendanceViewSet,
    CourseEnrollmentViewSet,
    CourseViewSet,
    GradeViewSet,
    SubjectViewSet,
    UserViewSet,
)

__all__ = [
    "UserViewSet",
    "CourseViewSet",
    "SubjectViewSet",
    "CourseEnrollmentViewSet",
    "GradeViewSet",
    "AttendanceViewSet",
]
