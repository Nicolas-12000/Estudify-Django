"""
URLs para la aplicación de usuarios.
"""
from django.urls import path

from apps.users import views

app_name = 'users'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Registro deshabilitado - solo admins crean usuarios desde el panel

    # Perfil (profile_view maneja tanto visualización como edición)
    path('profile/', views.profile_view, name='profile'),

    # Gestión de usuarios (admin)
    path('list/', views.user_list_view, name='user_list'),
    path('<int:pk>/', views.user_detail_view, name='user_detail'),
    path('<int:pk>/toggle/', views.toggle_user_status, name='toggle_status'),
]
