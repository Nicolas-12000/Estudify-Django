from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('asistencias/nueva/', views.attendance_create, name='attendance_create'),
    path('asistencias/', views.attendance_list, name='attendance_list'),
    path('calificaciones/', views.grades_list, name='grades_list'),
    path('importar/', views.import_grades, name='import_grades'),
    path('calificaciones/nueva/', views.grade_create, name='grades_create'),
    # Puedes agregar más rutas aquí
]
