from django.urls import path
from .views.logging import client_log
from .views.autocomplete import SiteAutocompleteView, UserAutocompleteView
from .views.auth import login_view
from .views.pointage import create_pointage, create_anomalie, scan_qr_view, create_pointage_via_qr
from .views.home import home_view

urlpatterns = [
    # Page d'accueil
    path('home/', home_view, name='home'),
    
    # Authentication
    path('login/', login_view, name='login'),
    
    # Pointage
    path('pointage/create/', create_pointage, name='create_pointage'),
    path('anomalie/create/', create_anomalie, name='create_anomalie'),
    path('scan-qr/', scan_qr_view, name='scan_qr'),
    path('pointage/qr/', create_pointage_via_qr, name='create_pointage_via_qr'),
    
    # Routes d'autocomplete déplacées hors du système d'admin
    path('api/autocomplete/site/', SiteAutocompleteView.as_view(), name='site-autocomplete'),
    path('api/autocomplete/user/', UserAutocompleteView.as_view(), name='user-autocomplete'),
    
    # Conserver les anciennes routes pour la compatibilité
    path('admin/core/site/autocomplete/', SiteAutocompleteView.as_view(), name='admin-site-autocomplete'),
    path('admin/core/user/autocomplete/', UserAutocompleteView.as_view(), name='admin-user-autocomplete'),
    
    path('api/logs/', client_log, name='client_log'),
] 