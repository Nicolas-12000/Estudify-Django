from django.urls import path
from .views import home, panel_admin, panel_profesor, panel_estudiante

urlpatterns = [
    path('', home, name='home'),
    path('panel-admin/', panel_admin, name='panel_admin'),
    path('panel-profesor/', panel_profesor, name='panel_profesor'),
    path('panel-estudiante/', panel_estudiante, name='panel_estudiante'),
]
