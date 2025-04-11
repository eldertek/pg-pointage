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
    help = 'Répare les pointages et les anomalies en supprimant toutes les anomalies existantes, ' \
           'en recalculant le statut des pointages et en recherchant les nouvelles anomalies'

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

    def handle(self, *args, **options):
        # Configurer le logger
        logger = logging.getLogger(__name__)
        log_level = logging.INFO
        if options['verbose']:
            log_level = logging.DEBUG
        logger.setLevel(log_level)

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

        # Commencer la réparation
        try:
            with transaction.atomic():
                # 1. Supprimer toutes les anomalies existantes
                anomalies_count = self._delete_anomalies(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                self.stdout.write(self.style.SUCCESS(f"{anomalies_count} anomalies supprimées"))

                # 2. Recalculer le statut de tous les pointages
                timesheets_count = self._recalculate_timesheet_status(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                self.stdout.write(self.style.SUCCESS(f"{timesheets_count} pointages recalculés"))

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

        if not dry_run:
            # Réinitialiser les statuts des pointages
            for timesheet in query:
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

                self.stdout.write(f"Pointage {timesheet.id} recalculé: {timesheet.timestamp} - {timesheet.get_entry_type_display()}")

        return count

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

        # Parcourir les pointages par date et par employé/site
        dates = query.values_list('timestamp__date', flat=True).distinct()
        sites = query.values_list('site_id', flat=True).distinct() if not site_id else [site_id]
        employees = query.values_list('employee_id', flat=True).distinct() if not employee_id else [employee_id]

        anomalies_created = 0

        for date in dates:
            for site_id in sites:
                for employee_id in employees:
                    # Vérifier s'il y a des pointages pour cette combinaison
                    has_timesheets = Timesheet.objects.filter(
                        timestamp__date=date,
                        site_id=site_id,
                        employee_id=employee_id
                    ).exists()

                    if has_timesheets:
                        # Appeler la méthode de scan d'anomalies
                        scan_view._scan_anomalies_for_date(
                            date=date,
                            site_id=site_id,
                            employee_id=employee_id,
                            force_update=True
                        )

                        self.stdout.write(f"Anomalies scannées pour le {date} - Site: {site_id} - Employé: {employee_id}")

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
