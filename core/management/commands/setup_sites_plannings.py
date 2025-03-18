from django.core.management.base import BaseCommand
from core.models import Site, Planning, Pointage, Anomalie
from datetime import time

class Command(BaseCommand):
    help = 'Configure les sites et leurs plannings'

    def handle(self, *args, **options):
        # Suppression des données existantes
        Pointage.objects.all().delete()
        Planning.objects.all().delete()
        Site.objects.all().delete()
        self.stdout.write('Données existantes supprimées.')

        # Création du site Georges V
        site_georges_v = Site.objects.create(
            name='Georges V - Paris 8',
            qr_code_value='SITE-0001',
            marge_retard=15,
            marge_depart_anticip=15,
            emails_alertes='quentin.poitrimoult@gmail.com'
        )
        self.stdout.write(f'Site créé : {site_georges_v.name}')

        # Création du site Mouffetard
        site_mouffetard = Site.objects.create(
            name='Mouffetard',
            qr_code_value='SITE-0002',
            marge_retard=15,
            marge_depart_anticip=10,
            emails_alertes='quentin.poitrimoult@gmail.com'
        )
        self.stdout.write(f'Site créé : {site_mouffetard.name}')

        # Création des plannings FIXE pour Georges V
        # Planning lundi/mercredi/vendredi
        Planning.objects.create(
            site=site_georges_v,
            type='FIXE',
            jours_passage='lundi,mercredi,vendredi',
            heure_debut_matin='08:00',
            heure_fin_matin='12:00',
            heure_debut_aprem='14:00',
            heure_fin_aprem='18:00',
            marge_pop_up=30
        )

        # Planning mardi/jeudi
        Planning.objects.create(
            site=site_georges_v,
            type='FIXE',
            jours_passage='mardi,jeudi',
            heure_debut_matin='09:00',
            heure_fin_matin='13:00',
            heure_debut_aprem='15:00',
            heure_fin_aprem='19:00',
            marge_pop_up=30
        )

        # Création des plannings FREQUENCE pour Mouffetard
        # Planning lundi et vendredi (2h)
        Planning.objects.create(
            site=site_mouffetard,
            type='FREQUENCE',
            jours_passage='lundi,vendredi',
            duree_prevue_minutes=120
        )

        # Planning mercredi (6h)
        Planning.objects.create(
            site=site_mouffetard,
            type='FREQUENCE',
            jours_passage='mercredi',
            duree_prevue_minutes=360
        )

        self.stdout.write(self.style.SUCCESS('Configuration terminée avec succès !')) 