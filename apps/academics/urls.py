from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Calificaciones
    path('calificaciones/', views.grades_list, name='grades_list'),
    path('calificaciones/nueva/', views.grade_create, name='grade_create'),

    # Asistencias
    path('asistencias/', views.attendance_list, name='attendance_list'),
    path('asistencias/nueva/', views.attendance_create, name='attendance_create'), 

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/api/grades/average/', views.api_grades_average, name='api_grades_average'),
    path('dashboard/api/attendance/monthly/', views.api_attendance_monthly, name='api_attendance_monthly'),

    # Importación
    path('importar/', views.import_grades, name='import_grades'),
]
