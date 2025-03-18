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
from django.urls import path, include
from django.shortcuts import redirect

# Vue pour rediriger vers la page d'accueil
def redirect_to_home(request):
    return redirect('home')

urlpatterns = [
    # Redirection de la racine vers la page d'accueil
    path('', redirect_to_home, name='root'),
    
    # Interface d'administration
    path('admin/', admin.site.urls, name='admin'),
    
    # Inclure toutes les URLs de l'application core
    path('', include('core.urls')),
    
    # Remarque : les routes suivantes sont commentées car elles sont désormais
    # définies dans core/urls.py et incluses via la ligne ci-dessus
    # path('login/', login_view, name='login'),
    # path('api/pointages', create_pointage, name='api-pointages'),
    # path('api/anomalies', create_anomalie, name='api-anomalies'),
    # path('api/pointages/scan', create_pointage_via_qr, name='api-pointages-scan'),
    # path('scan_qr/', scan_qr_view, name='scan_qr'),
]
