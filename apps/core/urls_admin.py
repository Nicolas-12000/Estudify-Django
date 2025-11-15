"""
URLs para el panel de administración.
"""
from django.urls import path
from apps.core import views_admin

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views_admin.admin_dashboard, name='dashboard'),
    
    # Gestión de Usuarios
    path('users/', views_admin.user_list, name='user_list'),
    path('users/create/', views_admin.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views_admin.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views_admin.user_delete, name='user_delete'),
    
    # Gestión de Cursos
    path('courses/', views_admin.course_list, name='course_list'),
    path('courses/create/', views_admin.course_create, name='course_create'),
    path('courses/<int:pk>/', views_admin.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views_admin.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views_admin.course_delete, name='course_delete'),
    
    # Gestión de Materias
    path('subjects/', views_admin.subject_list, name='subject_list'),
    path('subjects/create/', views_admin.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views_admin.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views_admin.subject_delete, name='subject_delete'),
    
    # Gestión de Inscripciones
    path('enrollments/', views_admin.enrollment_list, name='enrollment_list'),
    path('enrollments/create/', views_admin.enrollment_create, name='enrollment_create'),
    path('enrollments/<int:pk>/delete/', views_admin.enrollment_delete, name='enrollment_delete'),
]
