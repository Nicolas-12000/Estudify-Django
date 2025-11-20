from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('attendance/export/', views.export_attendance_excel, name='export_attendance_excel'),
    path('grades/export/', views.export_grades_excel, name='export_grades_excel'),
    path('boletin/<int:student_id>/', views.download_boletin_pdf, name='download_boletin_pdf'),
    # Después puedes agregar:
    # path('pdf/', views.report_pdf, name='report_pdf'),
    # path('excel/', views.report_excel, name='report_excel'),
]
