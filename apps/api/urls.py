from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.api import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'enrollments', views.CourseEnrollmentViewSet, basename='enrollment')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('notifications/', include('apps.notifications.urls')),
]
