from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('asistencias/nueva/', views.attendance_create, name='attendance_create'),
    path('asistencias/', views.attendance_list, name='attendance_list'),
    path('calificaciones/', views.grades_list, name='grades_list'),
    path('importar/', views.import_grades, name='import_grades'),
    path('calificaciones/nueva/', views.grade_create, name='grades_create'),
    path('asistencias/masiva/', views.attendance_bulk, name='attendance_bulk'),
    # Puedes agregar más rutas aquí
    path('estudiantes/', views.student_list, name='student_list'),
    path('estudiantes/create/', views.student_create, name='student_create'),
    path('estudiantes/<int:pk>/edit/', views.student_edit, name='student_edit'),
    # Estadísticas para Chart.js
    path('stats/subjects/', views.stats_subject_performance, name='stats_subject_performance'),
    path('stats/attendance/', views.stats_attendance_monthly, name='stats_attendance_monthly'),
]
