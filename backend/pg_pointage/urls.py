from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Planète Gardiens Pointage API",
        default_version='v1',
        description="API pour l'application de pointage Planète Gardiens",
        contact=openapi.Contact(email="contact@planetegardiens.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/organizations/', include('organizations.urls')),
    path('api/v1/sites/', include('sites.urls')),
    path('api/v1/timesheets/', include('timesheets.urls')),
    path('api/v1/alerts/', include('alerts.urls')),
    path('api/v1/reports/', include('reports.urls')),
    
    # Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

