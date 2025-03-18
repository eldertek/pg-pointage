import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planete_pointage.settings')
django.setup()

from core.models import Site, Planning

# Création du planning FIXE
site_fixe = Site.objects.get(name='Mouffetard - Paris 6')
planning_fixe = Planning.objects.create(
    site=site_fixe,
    type='FIXE',
    jours_passage='lundi,mardi,mercredi,jeudi,vendredi',
    actif=True,
    heure_debut_matin=time(8, 0),
    heure_fin_matin=time(12, 0),
    heure_debut_aprem=time(14, 0),
    heure_fin_aprem=time(18, 0),
    marge_retard=15,
    marge_depart_anticip=15
)

# Création du planning FREQUENCE
site_frequence = Site.objects.get(name='Georges V - Paris 8')
planning_frequence = Planning.objects.create(
    site=site_frequence,
    type='FREQUENCE',
    jours_passage='lundi,mardi,mercredi,jeudi,vendredi',
    actif=True,
    duree_prevue_minutes=120,
    marge_duree_pct=10
)

print(f'Planning FIXE créé: {planning_fixe}')
print(f'Planning FREQUENCE créé: {planning_frequence}') 