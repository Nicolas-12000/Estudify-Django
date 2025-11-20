from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('boletin/<int:student_id>/', views.student_report, name='student_report'),
    path('acta/<int:course_id>/', views.course_acta, name='course_acta'),
    path('acta/<int:course_id>/materia/<int:subject_id>/', views.course_acta, name='course_acta_subject'),
]
