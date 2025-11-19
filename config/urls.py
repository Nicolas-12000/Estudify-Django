from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
)

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Panel admin propio (si tienes un urls_admin.py dentro de apps.core)
    # Si no existe, puedes quitar esta línea.
    path('panel/', include('apps.core.urls_admin')),

    # Documentación API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API REST
    path('api/', include('apps.api.urls')),

    # Apps principales
    path('accounts/', include('apps.users.urls')),           # Usuarios (login, registro, perfiles)
    path('courses/', include('apps.courses.urls')),          # Cursos
    path('academics/', include('apps.academics.urls')),      # Académicos
    path('reports/', include('apps.reports.urls')),          # Reportes

    # Dashboard web principal y paneles personalizados
    path('', include('apps.core.urls')),                     # Panel admin, profesor, estudiante y home
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalización títulos del panel de administración Django
admin.site.site_header = 'Estudify - Administración'
admin.site.site_title = 'Estudify Admin'
admin.site.index_title = 'Panel de Administración'
