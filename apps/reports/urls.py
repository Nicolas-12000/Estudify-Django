from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    # Puedes agregar más rutas después para PDFs, Excel, etc.
]
