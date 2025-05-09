from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/dashboard/', include('dashboard.urls')),
    path('api/v1/sites/', include('sites.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/timesheets/', include('timesheets.urls')),
    path('api/v1/alerts/', include('alerts.urls')),
    path('api/v1/organizations/', include('organizations.urls')),
    path('api/v1/reports/', include('reports.urls')),
    
    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

