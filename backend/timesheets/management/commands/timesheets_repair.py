import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from timesheets.models import Timesheet, Anomaly
from sites.models import Site, SiteEmployee, Schedule, ScheduleDetail
from users.models import User
from timesheets.views import ScanAnomaliesView


class Command(BaseCommand):
    help = '''
    Répare les pointages et les anomalies en supprimant toutes les anomalies existantes,
    en recalculant le statut des pointages et en recherchant les nouvelles anomalies.

    Exemples d'utilisation :

    # Réparer tous les pointages des 30 derniers jours
    python manage.py timesheets_repair

    # Réparer les pointages d'une période spécifique
    python manage.py timesheets_repair --start-date 2025-04-01 --end-date 2025-04-30

    # Réparer les pointages d'un site spécifique
    python manage.py timesheets_repair --site 1

    # Réparer les pointages d'un employé spécifique
    python manage.py timesheets_repair --employee 1

    # Exécuter en mode simulation sans modifier la base de données
    python manage.py timesheets_repair --dry-run

    # Afficher des informations détaillées pendant l'exécution
    python manage.py timesheets_repair --verbose
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
            help='Date de début au format YYYY-MM-DD (par défaut: 30 jours avant aujourd\'hui)'
        )
        parser.add_argument(
            '--end-date',
            type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
            help='Date de fin au format YYYY-MM-DD (par défaut: aujourd\'hui)'
        )
        parser.add_argument(
            '--site',
            type=int,
            help='ID du site à traiter (par défaut: tous les sites)'
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='ID de l\'employé à traiter (par défaut: tous les employés)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exécuter en mode simulation sans modifier la base de données'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher des informations détaillées pendant l\'exécution'
        )
        parser.add_argument(
            '--ignore-errors',
            action='store_true',
            help='Ignorer les erreurs et continuer le traitement'
        )
        parser.add_argument(
            '--skip-validation',
            action='store_true',
            help='Ignorer les validations lors de la sauvegarde des pointages'
        )

    def handle(self, *args, **options):
        # Configurer le logger
        logger = logging.getLogger(__name__)
        log_level = logging.INFO
        if options['verbose']:
            log_level = logging.DEBUG
        logger.setLevel(log_level)

        # Initialiser les options
        self.skip_validation = options.get('skip_validation', False)
        self.ignore_errors = options.get('ignore_errors', False)

        # Configurer les dates
        end_date = options['end_date'] or timezone.now().date()
        start_date = options['start_date'] or (end_date - timedelta(days=30))

        # Afficher les paramètres
        self.stdout.write(self.style.SUCCESS(f"Réparation des pointages du {start_date} au {end_date}"))
        if options['site']:
            try:
                site = Site.objects.get(pk=options['site'])
                self.stdout.write(f"Site: {site.name} (ID: {site.id})")
            except Site.DoesNotExist:
                raise CommandError(f"Site avec ID {options['site']} non trouvé")
        else:
            self.stdout.write("Tous les sites seront traités")

        if options['employee']:
            try:
                employee = User.objects.get(pk=options['employee'])
                self.stdout.write(f"Employé: {employee.get_full_name()} (ID: {employee.id})")
            except User.DoesNotExist:
                raise CommandError(f"Employé avec ID {options['employee']} non trouvé")
        else:
            self.stdout.write("Tous les employés seront traités")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("Mode simulation activé - aucune modification ne sera effectuée"))

        if self.skip_validation:
            self.stdout.write(self.style.WARNING("Validation des pointages désactivée - les pointages seront sauvegardés sans validation"))

        if self.ignore_errors:
            self.stdout.write(self.style.WARNING("Ignorer les erreurs activé - les erreurs seront ignorées et le traitement continuera"))

        # Commencer la réparation
        try:
            with transaction.atomic():
                # 1. Supprimer toutes les anomalies existantes
                anomalies_count = self._delete_anomalies(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                self.stdout.write(self.style.SUCCESS(f"{anomalies_count} anomalies supprimées"))

                # 2. Recalculer le statut de tous les pointages
                processed_count = self._recalculate_timesheet_status(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                self.stdout.write(self.style.SUCCESS(f"{processed_count} pointages recalculés"))

                # 3. Rechercher les nouvelles anomalies
                new_anomalies_count = self._scan_anomalies(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                self.stdout.write(self.style.SUCCESS(f"{new_anomalies_count} nouvelles anomalies détectées"))

                if options['dry_run']:
                    # Annuler la transaction en mode simulation
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.WARNING("Mode simulation - toutes les modifications ont été annulées"))

            self.stdout.write(self.style.SUCCESS("Réparation terminée avec succès"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la réparation: {str(e)}"))
            logger.error(f"Erreur lors de la réparation: {str(e)}", exc_info=True)
            raise CommandError(f"Erreur lors de la réparation: {str(e)}")

    def _delete_anomalies(self, start_date, end_date, site_id=None, employee_id=None, dry_run=False):
        """Supprime toutes les anomalies existantes dans la période spécifiée"""
        query = Anomaly.objects.filter(date__gte=start_date, date__lte=end_date)

        if site_id:
            query = query.filter(site_id=site_id)

        if employee_id:
            query = query.filter(employee_id=employee_id)

        count = query.count()

        if not dry_run:
            query.delete()

        return count

    def _recalculate_timesheet_status(self, start_date, end_date, site_id=None, employee_id=None, dry_run=False):
        """Recalcule le statut de tous les pointages dans la période spécifiée"""
        query = Timesheet.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

        if site_id:
            query = query.filter(site_id=site_id)

        if employee_id:
            query = query.filter(employee_id=employee_id)

        count = query.count()
        processed_count = 0
        error_count = 0

        if not dry_run:
            # Réinitialiser les statuts des pointages
            for timesheet in query:
                try:
                    # Réinitialiser les champs de statut
                    timesheet.is_late = False
                    timesheet.late_minutes = 0
                    timesheet.is_early_departure = False
                    timesheet.early_departure_minutes = 0
                    timesheet.is_out_of_schedule = False
                    timesheet.is_ambiguous = False

                    # Appeler la logique de correspondance de planning
                    from timesheets.views import TimesheetCreateView
                    view = TimesheetCreateView()
                    view._match_schedule_and_check_anomalies(timesheet)

                    # Sauvegarder le pointage sans validation si l'option est activée
                    if self.skip_validation:
                        # Sauvegarder directement sans appeler clean()
                        from django.db import connection
                        cursor = connection.cursor()
                        cursor.execute(
                            "UPDATE timesheets_timesheet SET is_late = %s, late_minutes = %s, "
                            "is_early_departure = %s, early_departure_minutes = %s, "
                            "is_out_of_schedule = %s, is_ambiguous = %s "
                            "WHERE id = %s",
                            [timesheet.is_late, timesheet.late_minutes,
                             timesheet.is_early_departure, timesheet.early_departure_minutes,
                             timesheet.is_out_of_schedule, timesheet.is_ambiguous,
                             timesheet.id]
                        )
                    else:
                        # Sauvegarder normalement avec validation
                        timesheet.save()

                    processed_count += 1
                    self.stdout.write(f"Pointage {timesheet.id} recalculé: {timesheet.timestamp} - {timesheet.get_entry_type_display()}")

                except Exception as e:
                    error_count += 1
                    error_message = str(e)
                    self.stdout.write(self.style.ERROR(f"Erreur lors du recalcul du pointage {timesheet.id}: {error_message}"))

                    # Si l'option ignore-errors n'est pas activée, lever l'exception
                    if not self.ignore_errors:
                        raise

        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"{error_count} erreurs rencontrées lors du recalcul des pointages"))

        return processed_count

    def _scan_anomalies(self, start_date, end_date, site_id=None, employee_id=None, dry_run=False):
        """Recherche les nouvelles anomalies dans la période spécifiée"""
        if dry_run:
            # En mode simulation, compter les anomalies qui seraient créées
            # sans les créer réellement
            return 0

        # Utiliser directement la logique de ScanAnomaliesView pour éviter les problèmes de requête factice
        from timesheets.models import Timesheet, Anomaly
        from django.db.models import Q

        # Préparer la requête pour récupérer les pointages
        query = Timesheet.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

        if site_id:
            query = query.filter(site_id=site_id)

        if employee_id:
            query = query.filter(employee_id=employee_id)

        # Compter les anomalies avant
        anomalies_before = Anomaly.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        if site_id:
            anomalies_before = anomalies_before.filter(site_id=site_id)

        if employee_id:
            anomalies_before = anomalies_before.filter(employee_id=employee_id)

        anomalies_count_before = anomalies_before.count()

        # Utiliser la vue ScanAnomaliesView pour détecter les anomalies
        scan_view = ScanAnomaliesView()

        # Créer un objet Request factice pour appeler la méthode post
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()

        # Parcourir les pointages par date
        dates = query.values_list('timestamp__date', flat=True).distinct()

        for date in dates:
            # Préparer les données pour la requête
            data = {
                'start_date': date,
                'end_date': date,
                'force_update': True
            }

            if site_id:
                data['site'] = site_id

            if employee_id:
                data['employee'] = employee_id

            # Créer une requête factice
            request = factory.post('/api/timesheets/scan-anomalies/', data, format='json')

            # Appeler la méthode post
            try:
                response = scan_view.post(request)
                self.stdout.write(f"Anomalies scannées pour le {date}")
                if site_id:
                    self.stdout.write(f"  Site: {site_id}")
                if employee_id:
                    self.stdout.write(f"  Employé: {employee_id}")
                self.stdout.write(f"  Résultat: {response.data.get('message', 'Aucun message')}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors du scan des anomalies pour le {date}: {str(e)}")
                )

        # Compter les anomalies après
        anomalies_after = Anomaly.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        if site_id:
            anomalies_after = anomalies_after.filter(site_id=site_id)

        if employee_id:
            anomalies_after = anomalies_after.filter(employee_id=employee_id)

        anomalies_count_after = anomalies_after.count()

        # Calculer le nombre d'anomalies créées
        return anomalies_count_after - anomalies_count_before
