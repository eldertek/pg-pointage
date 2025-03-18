from django.core.management.base import BaseCommand
from core.models import Planning, Site
from datetime import time

class Command(BaseCommand):
    help = 'Crée un planning avec ses horaires'

    def add_arguments(self, parser):
        parser.add_argument('--site', type=str, help='Nom du site')
        parser.add_argument('--type', type=str, choices=['FIXE', 'FREQUENCE'], default='FIXE', help='Type de planning')
        parser.add_argument('--jours', type=str, help='Jours de passage (ex: lundi,mardi,mercredi,jeudi,vendredi)')
        parser.add_argument('--debut-matin', type=str, help='Heure de début le matin (format HH:MM)')
        parser.add_argument('--fin-matin', type=str, help='Heure de fin le matin (format HH:MM)')
        parser.add_argument('--debut-aprem', type=str, help='Heure de début l\'après-midi (format HH:MM)')
        parser.add_argument('--fin-aprem', type=str, help='Heure de fin l\'après-midi (format HH:MM)')
        parser.add_argument('--duree', type=int, help='Durée prévue en minutes (pour planning FREQUENCE)')
        parser.add_argument('--marge', type=int, default=30, help='Marge pour la fenêtre interactive en minutes (pour planning FREQUENCE)')

    def handle(self, *args, **options):
        try:
            # Récupérer ou créer le site
            site_name = options['site'] or "Georges V - Paris 8"
            site = Site.objects.get(name=site_name)
            
            # Créer le planning
            planning = Planning(
                site=site,
                type=options['type'],
                jours_passage=options['jours'] or 'lundi,mardi,mercredi,jeudi,vendredi'
            )
            
            if planning.type == 'FIXE':
                # Convertir les heures de format HH:MM en objets time
                debut_matin = options['debut_matin'] or '08:00'
                fin_matin = options['fin_matin'] or '12:00'
                debut_aprem = options['debut_aprem'] or '14:00'
                fin_aprem = options['fin_aprem'] or '18:00'
                
                planning.heure_debut_matin = time(*map(int, debut_matin.split(':')))
                planning.heure_fin_matin = time(*map(int, fin_matin.split(':')))
                planning.heure_debut_aprem = time(*map(int, debut_aprem.split(':')))
                planning.heure_fin_aprem = time(*map(int, fin_aprem.split(':')))
                
                self.stdout.write("Planning FIXE créé avec les horaires suivants :")
                self.stdout.write(f"Matin : {debut_matin} - {fin_matin}")
                self.stdout.write(f"Après-midi : {debut_aprem} - {fin_aprem}")
            else:
                planning.duree_prevue_minutes = options['duree'] or 480
                planning.marge_pop_up = options['marge']
                self.stdout.write(f"Planning FREQUENCE créé avec une durée de {planning.duree_prevue_minutes} minutes")
                self.stdout.write(f"Marge de la fenêtre interactive : {planning.marge_pop_up} minutes")
            
            planning.save()
            self.stdout.write(self.style.SUCCESS(f"Planning créé avec succès pour {site.name}"))
                
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Le site '{site_name}' n'existe pas")) 