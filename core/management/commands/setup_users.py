from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Configure les utilisateurs initiaux'

    def handle(self, *args, **options):
        # Suppression des utilisateurs existants
        User.objects.all().delete()
        self.stdout.write('Utilisateurs existants supprimés.')

        # Création du superadmin (User n°1)
        superadmin = User.objects.create_superuser(
            username='Kent',
            email='quentin.poitrimoult@gmail.com',
            password='azertyui',
            role='manager'
        )
        self.stdout.write(f'Superadmin créé : {superadmin.username}')

        # Création du gardien (User n°2)
        gardien = User.objects.create_user(
            username='Kenttest',
            email='admin95@planete-gardiens.com',
            password='qsdfghjk',
            role='gardien'
        )
        self.stdout.write(f'Gardien créé : {gardien.username}')

        # Création de l'agent de nettoyage (User n°3)
        agent = User.objects.create_user(
            username='Kenttest2',
            email='exploitation95@planete-gardiens.com',
            password='aqzsedrf',
            role='agent_de_nettoyage'
        )
        self.stdout.write(f'Agent de nettoyage créé : {agent.username}')

        self.stdout.write(self.style.SUCCESS('Configuration des utilisateurs terminée avec succès !')) 