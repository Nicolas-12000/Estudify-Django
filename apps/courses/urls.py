from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('nuevo/', views.course_create, name='course_create'),
    path('<int:pk>/editar/', views.course_edit, name='course_edit'),
]
