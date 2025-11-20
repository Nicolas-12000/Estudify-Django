from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Cursos
    path('', views.course_list, name='course_list'),
    path('nuevo/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/editar/', views.course_edit, name='course_edit'),
    path('<int:pk>/eliminar/', views.course_delete, name='course_delete'),

    # Materias
    path('materias/', views.subject_list, name='subject_list'),
    path('materias/nueva/', views.subject_create, name='subject_create'),
    path('materias/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('materias/<int:pk>/editar/', views.subject_edit, name='subject_edit'),
    path('materias/<int:pk>/eliminar/', views.subject_delete, name='subject_delete'),
]
