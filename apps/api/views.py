"""Compatibility re-exports for API viewsets.

Some places import from `apps.api.views`, while the real implementations
live under `apps.api.v1.viewsets`. This module re-exports the common
ViewSet classes so both import styles work.
"""
from apps.api.v1.viewsets import (AttendanceViewSet, CourseEnrollmentViewSet,
                                  CourseViewSet, GradeViewSet, SubjectViewSet,
                                  UserViewSet)

__all__ = [
    'UserViewSet',
    'CourseViewSet',
    'SubjectViewSet',
    'CourseEnrollmentViewSet',
    'GradeViewSet',
    'AttendanceViewSet',
]
