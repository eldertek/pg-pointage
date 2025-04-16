import os
import logging
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = '''
    Sauvegarde la base de données PostgreSQL dans un fichier SQL.
    Cette commande est conçue pour être exécutée tous les jours à 00h00 via un cron job.

    Exemples d'utilisation :

    # Sauvegarder la base de données avec les paramètres par défaut
    python manage.py backup_database

    # Spécifier un répertoire de sauvegarde personnalisé
    python manage.py backup_database --backup-dir /chemin/vers/sauvegardes

    # Utiliser une URL de connexion à la base de données
    python manage.py backup_database --database-url postgres://user:password@host:port/dbname

    # Conserver les sauvegardes pendant un nombre de jours spécifique
    python manage.py backup_database --retention-days 30

    # Exécuter en mode simulation sans créer de sauvegarde
    python manage.py backup_database --dry-run

    # Afficher des informations détaillées pendant l'exécution
    python manage.py backup_database --verbose
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            help='Répertoire où stocker les sauvegardes (par défaut: /opt/pg-pointage/backups)'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Nombre de jours pendant lesquels conserver les sauvegardes (par défaut: 30)'
        )
        parser.add_argument(
            '--database-url',
            type=str,
            help='URL de connexion à la base de données (format: postgres://user:password@host:port/dbname)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exécuter en mode simulation sans créer de sauvegarde'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher des informations détaillées pendant l\'exécution'
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        dry_run = options['dry_run']
        retention_days = options['retention_days']
        
        # Définir le répertoire de sauvegarde
        backup_dir = options['backup_dir'] or '/opt/pg-pointage/backups'
        
        # Créer le répertoire de sauvegarde s'il n'existe pas
        if not dry_run:
            os.makedirs(backup_dir, exist_ok=True)
            
        # Récupérer les informations de connexion à la base de données
        database_url = options['database_url'] or os.getenv('DATABASE_URL')
        
        if database_url:
            # Parser DATABASE_URL
            match = re.match(r'^postgres://(?P<user>.+?):(?P<password>.+?)@(?P<host>.+?):(?P<port>\d+)/(?P<name>.+?)$', database_url)
            if match:
                db_name = match.group('name')
                db_user = match.group('user')
                db_password = match.group('password')
                db_host = match.group('host')
                db_port = match.group('port')
            else:
                raise CommandError('Format de DATABASE_URL invalide')
        else:
            # Utiliser les paramètres de settings.py
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']
        
        # Générer le nom du fichier de sauvegarde avec la date et l'heure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{db_name}_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Afficher les informations de sauvegarde
        self.log_info(f"Base de données: {db_name}")
        self.log_info(f"Fichier de sauvegarde: {backup_path}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode simulation: aucune sauvegarde ne sera créée"))
            return
        
        # Exécuter pg_dump pour créer la sauvegarde
        try:
            # Définir la variable d'environnement PGPASSWORD pour éviter les invites de mot de passe
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            # Construire la commande pg_dump
            cmd = [
                'pg_dump',
                '--host', db_host,
                '--port', db_port,
                '--username', db_user,
                '--format', 'c',  # Format personnalisé (compressé)
                '--file', backup_path,
                db_name
            ]
            
            self.log_info(f"Exécution de la commande: {' '.join(cmd)}")
            
            # Exécuter la commande
            process = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Vérifier si la commande a réussi
            if process.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f"Sauvegarde créée avec succès: {backup_path}"))
                
                # Vérifier la taille du fichier
                file_size = os.path.getsize(backup_path)
                self.log_info(f"Taille du fichier: {self.format_size(file_size)}")
            else:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la sauvegarde: {process.stderr}"))
                raise CommandError(f"Échec de la sauvegarde: {process.stderr}")
            
            # Supprimer les anciennes sauvegardes
            self.cleanup_old_backups(backup_dir, retention_days)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la sauvegarde: {str(e)}"))
            raise CommandError(f"Échec de la sauvegarde: {str(e)}")
    
    def cleanup_old_backups(self, backup_dir, retention_days):
        """Supprime les sauvegardes plus anciennes que retention_days."""
        self.log_info(f"Nettoyage des sauvegardes plus anciennes que {retention_days} jours")
        
        # Calculer la date limite
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Parcourir les fichiers du répertoire de sauvegarde
        backup_dir_path = Path(backup_dir)
        count = 0
        
        for backup_file in backup_dir_path.glob('*.sql'):
            # Obtenir la date de modification du fichier
            file_mtime = datetime.fromtimestamp(os.path.getmtime(backup_file))
            
            # Supprimer le fichier s'il est plus ancien que la date limite
            if file_mtime < cutoff_date:
                self.log_info(f"Suppression de l'ancienne sauvegarde: {backup_file}")
                os.remove(backup_file)
                count += 1
        
        if count > 0:
            self.log_info(f"{count} anciennes sauvegardes supprimées")
        else:
            self.log_info("Aucune ancienne sauvegarde à supprimer")
    
    def log_info(self, message):
        """Affiche un message d'information si le mode verbose est activé."""
        if self.verbose:
            self.stdout.write(message)
        self.logger.info(message)
    
    def format_size(self, size_bytes):
        """Formate une taille en octets en une chaîne lisible."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
