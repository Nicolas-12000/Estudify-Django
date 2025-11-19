from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('asistencias/nueva/', views.attendance_create, name='attendance_create'), 
    path('asistencias/', views.attendance_list, name='attendance_list'),
    path('calificaciones/', views.grades_list, name='grades_list'),
    path('asistencias/', views.attendance_list, name='attendance_list'),
    path('importar/', views.import_grades, name='import_grades'),  # <---- AGREGA ESTA LÍNEA
    path('nueva/', views.grade_create, name='grades_create'),

    # Puedes agregar aquí más rutas
]
