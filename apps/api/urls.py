from rest_framework.routers import DefaultRouter
from django.urls import path, include
from apps.api import views

# Usar `DefaultRouter` para generar las rutas automáticamente en /api/
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'enrollments', views.CourseEnrollmentViewSet, basename='enrollment')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')

app_name = 'api'

urlpatterns = [
	# Rutas generadas por el router bajo /api/ (se incluyen desde config.urls)
	path('', include(router.urls)),

	# Autenticación de la API (login/logout browsable API)
	path('auth/', include('rest_framework.urls')),
]
