"""
URL configuration for planete_pointage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# API documentation
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Vue pour rediriger vers la page d'accueil
def redirect_to_home(request):
    return redirect('home')

# CSRF-exempt views for API authentication
csrf_exempt_auth = [
    path('api/token/', csrf_exempt(TokenObtainPairView.as_view()), name='token_obtain_pair'),
    path('api/token/refresh/', csrf_exempt(TokenRefreshView.as_view()), name='token_refresh'),
]

# Schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Planète Gardiens Pointage API",
        default_version='v1',
        description="API pour l'application Planète Gardiens Pointage",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Redirection de la racine vers la page d'accueil
    path('', redirect_to_home, name='root'),
    
    # Interface d'administration
    path('admin/', admin.site.urls, name='admin'),
    
    # Inclure toutes les URLs de l'application core
    path('', include('core.urls')),
    
    # JWT authentication endpoints
    path('', include(csrf_exempt_auth)),
    
    # API documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Add drf-yasg to INSTALLED_APPS
if 'drf_yasg' not in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS += ['drf_yasg']
