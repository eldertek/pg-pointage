from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

@login_required
def home_view(request):
    """
    Vue pour la page d'accueil qui affiche les principales fonctionnalités
    et des statistiques de base.
    """
    # Récupérer quelques statistiques de base (à adapter selon les besoins)
    from ..models import Pointage, Anomalie, Site, User
    
    # Obtenir la date d'aujourd'hui pour filtrer les pointages
    today = timezone.now().date()
    
    context = {
        'title': 'Tableau de bord - Planète Pointage',
        'stats': {
            'pointages_total': Pointage.objects.count(),
            'pointages_today': Pointage.objects.filter(date_scan__date=today).count(),
            'anomalies_pending': Anomalie.objects.filter(status='en_attente').count(),
            'sites_count': Site.objects.count(),
            'users_count': User.objects.count(),
        },
        'user': request.user,
        'is_admin': request.user.is_staff or request.user.is_superuser,
    }
    
    logger.info(f"Page d'accueil consultée par {request.user.username}")
    return render(request, 'core/home.html', context) 