"""
Ce fichier transforme le dossier views en package Python.
"""

# Import des vues
from .auth import login_view
from .pointage import create_pointage, create_anomalie, scan_qr_view, create_pointage_via_qr
from .logging import client_log
from .autocomplete import SiteAutocompleteView, UserAutocompleteView
from .home import home_view

# Export des vues
__all__ = [
    'login_view',
    'create_pointage',
    'create_anomalie',
    'scan_qr_view',
    'create_pointage_via_qr',
    'client_log',
    'SiteAutocompleteView',
    'UserAutocompleteView',
    'home_view',
] 