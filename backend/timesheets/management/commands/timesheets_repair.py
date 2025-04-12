import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.dispatch import receiver

from timesheets.models import Timesheet, Anomaly
from sites.models import Site, SiteEmployee, Schedule, ScheduleDetail
from users.models import User
from timesheets.views import ScanAnomaliesView
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.serializers import ValidationError


class Command(BaseCommand):
    help = '''
    Répare les pointages et les anomalies en supprimant toutes les anomalies existantes
    et en recréant les pointages dans l'ordre chronologique.

    Par défaut, la commande supprime et recrée les pointages dans l'ordre chronologique
    pour éviter les problèmes de validation liés à l'ordre des pointages.

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

    # Ignorer les validations lors de la sauvegarde des pointages
    python manage.py timesheets_repair --skip-validation

    # Ignorer les erreurs et continuer le traitement
    python manage.py timesheets_repair --ignore-errors

    # Ne pas supprimer et recréer les pointages (utiliser le recalcul simple)
    python manage.py timesheets_repair --no-recreate-entries
    '''

    def _is_timesheet_matching_schedule(self, timesheet, schedule):
        """Vérifie si un pointage correspond à un planning"""
        from sites.models import ScheduleDetail
        from datetime import datetime

        # Récupérer les informations nécessaires
        timestamp = timesheet.timestamp
        current_date = timestamp.date()
        current_weekday = current_date.weekday()  # 0 = Lundi, 6 = Dimanche
        current_time = timestamp.time()

        # Vérifier si le planning a des détails pour ce jour
        try:
            schedule_detail = ScheduleDetail.objects.get(
                schedule=schedule,
                day_of_week=current_weekday
            )

            # Pour les plannings fixes, vérifier les horaires
            if schedule.schedule_type == 'FIXED':
                # Vérifier les horaires du matin
                if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                    # Si l'heure est dans la plage du matin ou proche
                    if (schedule_detail.start_time_1 <= current_time <= schedule_detail.end_time_1):
                        return True

                # Vérifier les horaires de l'après-midi
                if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                    # Si l'heure est dans la plage de l'après-midi ou proche
                    if (schedule_detail.start_time_2 <= current_time <= schedule_detail.end_time_2):
                        return True

            # Pour les plannings fréquence, tout pointage est valide
            elif schedule.schedule_type == 'FREQUENCY':
                return True

        except ScheduleDetail.DoesNotExist:
            # Pas de planning pour ce jour
            return False

        return False

    def _is_schedule_active_for_date(self, schedule, date):
        """Vérifie si un planning est actif pour une date donnée"""
        from sites.models import ScheduleDetail

        # Vérifier si le planning a des détails pour ce jour
        try:
            schedule_detail = ScheduleDetail.objects.get(
                schedule=schedule,
                day_of_week=date.weekday()
            )
            return True
        except ScheduleDetail.DoesNotExist:
            return False

    def _find_employee_schedule(self, employee, site, date):
        """Trouve le planning associé à un employé et un site pour une date donnée."""
        from sites.models import SiteEmployee, ScheduleDetail

        self.stdout.write(f"Recherche du planning pour {employee.get_full_name()} (ID: {employee.id}) au site {site.name} (ID: {site.id}) le {date}")

        # Récupérer les relations site-employé pour cet employé et ce site
        site_employee_relations = SiteEmployee.objects.filter(
            site=site,
            employee=employee,
            is_active=True
        ).select_related('schedule')

        self.stdout.write(f"  {site_employee_relations.count()} relations site-employé trouvées")

        # Parcourir les relations pour trouver un planning actif pour cette date
        for site_employee in site_employee_relations:
            schedule = site_employee.schedule
            if not schedule or not schedule.is_active:
                self.stdout.write(f"  Relation {site_employee.id}: Pas de planning actif")
                continue

            # Afficher les informations détaillées du planning
            self.stdout.write(f"  Relation {site_employee.id}: Planning {schedule.id} - Type: {schedule.schedule_type}")

            # Afficher les marges de tolérance selon le type de planning
            if schedule.schedule_type == 'FIXED':
                self.stdout.write(f"    Marges de tolérance: Retard={schedule.late_arrival_margin or site.late_margin} min, "
                                 f"Départ anticipé={schedule.early_departure_margin or site.early_departure_margin} min")
            elif schedule.schedule_type == 'FREQUENCY':
                self.stdout.write(f"    Tolérance fréquence: {schedule.frequency_tolerance_percentage or site.frequency_tolerance}%")

            # Vérifier si le planning a des détails pour ce jour
            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=date.weekday()
                )

                # Afficher les détails du planning selon son type
                if schedule.schedule_type == 'FIXED':
                    day_type = schedule_detail.day_type
                    self.stdout.write(f"    Détails du planning pour {schedule_detail.get_day_of_week_display()} (jour {date.weekday()})")
                    self.stdout.write(f"    Type de journée: {schedule_detail.get_day_type_display()}")

                    if day_type in ['FULL', 'AM'] and schedule_detail.start_time_1 and schedule_detail.end_time_1:
                        self.stdout.write(f"    Matin: {schedule_detail.start_time_1}-{schedule_detail.end_time_1}")

                    if day_type in ['FULL', 'PM'] and schedule_detail.start_time_2 and schedule_detail.end_time_2:
                        self.stdout.write(f"    Après-midi: {schedule_detail.start_time_2}-{schedule_detail.end_time_2}")
                elif schedule.schedule_type == 'FREQUENCY':
                    self.stdout.write(f"    Détails du planning fréquence pour {schedule_detail.get_day_of_week_display()} (jour {date.weekday()})")
                    self.stdout.write(f"    Durée attendue: {schedule_detail.frequency_duration} minutes")

                # Planning trouvé pour ce jour
                return schedule
            except ScheduleDetail.DoesNotExist:
                self.stdout.write(f"  Pas de détails de planning pour le jour {date.weekday()}")
                # Pas de planning pour ce jour
                continue

        # Aucun planning trouvé
        self.stdout.write(f"  Aucun planning correspondant trouvé")
        return None

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
        parser.add_argument(
            '--no-recreate-entries',
            action='store_true',
            help='Ne pas supprimer et recréer les pointages (utiliser le recalcul simple)'
        )

    def handle(self, *args, **options):
        # Configurer le logger
        logger = logging.getLogger(__name__)
        log_level = logging.INFO
        if options['verbose']:
            log_level = logging.DEBUG
            # Configurer également les loggers des vues pour capturer tous les logs
            logging.getLogger('timesheets.views').setLevel(logging.DEBUG)
            # Configurer le logger racine pour capturer tous les logs
            logging.getLogger().setLevel(logging.DEBUG)
            # Ajouter un handler pour afficher les logs dans la console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)

            # Log pour confirmer que le mode verbose est activé
            logger.debug("Mode verbose activé - tous les logs seront affichés")
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

                # 2. Par défaut, supprimer et recréer les pointages, sauf si l'option no-recreate-entries est activée
                if options.get('no_recreate_entries', False):
                    # Recalculer le statut des pointages existants
                    processed_count = self._recalculate_timesheet_status(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                    self.stdout.write(self.style.SUCCESS(f"{processed_count} pointages recalculés"))
                else:
                    # Supprimer et recréer les pointages
                    processed_count = self._recreate_timesheet_entries(start_date, end_date, options['site'], options['employee'], options['dry_run'])
                    self.stdout.write(self.style.SUCCESS(f"{processed_count} pointages recréés"))

                # 3. Effectuer un scan d'anomalies complet après avoir recréé tous les pointages
                if not options['dry_run']:
                    self.stdout.write("Exécution d'un scan d'anomalies complet...")
                    from timesheets.views import ScanAnomaliesView
                    from rest_framework.test import APIRequestFactory
                    from django.contrib.auth import get_user_model
                    from rest_framework.test import force_authenticate

                    # Créer une requête factice
                    factory = APIRequestFactory()
                    data = {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'force_update': True
                    }

                    # Ajouter les filtres optionnels
                    if options['site']:
                        data['site'] = options['site']
                    if options['employee']:
                        data['employee'] = options['employee']

                    request = factory.post('/api/timesheets/scan-anomalies/', data, format='json')

                    # Authentifier la requête avec un superadmin
                    User = get_user_model()
                    admin_user = User.objects.filter(is_super_admin=True).first()
                    if not admin_user:
                        admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        force_authenticate(request, user=admin_user)

                    # Exécuter la vue
                    view = ScanAnomaliesView.as_view()
                    response = view(request)

                    # Afficher les résultats
                    if hasattr(response, 'data'):
                        self.stdout.write(self.style.SUCCESS(f"Scan d'anomalies terminé: {response.data.get('message', 'Aucun message')}"))
                        if options['verbose']:
                            self.stdout.write(f"Détails de la réponse: {response.data}")
                    else:
                        self.stdout.write(self.style.WARNING(f"Scan d'anomalies terminé sans réponse de données"))

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

    def _recreate_timesheet_entries(self, start_date, end_date, site_id=None, employee_id=None, dry_run=False):
        """Supprime et recrée les pointages dans l'ordre chronologique"""
        # Configurer le logger
        logger = logging.getLogger(__name__)

        # Récupérer tous les pointages pour la période spécifiée
        query = Timesheet.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

        if site_id:
            query = query.filter(site_id=site_id)

        if employee_id:
            query = query.filter(employee_id=employee_id)

        # Ordonner les pointages par timestamp croissant (du plus ancien au plus récent)
        query = query.order_by('timestamp')

        # Stocker les pointages en mémoire avant de les supprimer
        timesheet_data = []
        for timesheet in query:
            # Stocker toutes les données nécessaires pour recréer le pointage
            timesheet_data.append({
                'employee_id': timesheet.employee_id,
                'site_id': timesheet.site_id,
                'timestamp': timesheet.timestamp,
                'entry_type': timesheet.entry_type,
                'scan_type': timesheet.scan_type,
                'latitude': timesheet.latitude,
                'longitude': timesheet.longitude,
                'created_at': timesheet.created_at,
                'updated_at': timesheet.updated_at
            })

        # Compter le nombre de pointages à recréer
        count = len(timesheet_data)
        self.stdout.write(f"Suppression et recréation de {count} pointages")

        if dry_run:
            return count

        # Supprimer tous les pointages
        query.delete()
        self.stdout.write(f"{count} pointages supprimés")

        # Recréer les pointages dans l'ordre chronologique
        processed_count = 0
        error_count = 0

        # Désactiver temporairement les signaux pour éviter les effets secondaires
        from django.db.models.signals import pre_save, post_save
        from django.dispatch import receiver

        # Sauvegarder les récepteurs actuels
        saved_pre_save_receivers = pre_save.receivers
        saved_post_save_receivers = post_save.receivers

        # Vider les récepteurs
        pre_save.receivers = []
        post_save.receivers = []

        try:
            # Recréer les pointages
            for data in timesheet_data:
                try:
                    # Créer un nouveau pointage avec les données sauvegardées
                    timesheet = Timesheet(
                        employee_id=data['employee_id'],
                        site_id=data['site_id'],
                        timestamp=data['timestamp'],
                        entry_type=data['entry_type'],
                        scan_type=data['scan_type'],
                        latitude=data['latitude'],
                        longitude=data['longitude']
                    )

                    # Sauvegarder sans validation
                    if self.skip_validation:
                        # Sauvegarder directement sans appeler clean()
                        timesheet.save()
                        # Mettre à jour les champs created_at et updated_at
                        from django.db import connection
                        cursor = connection.cursor()
                        cursor.execute(
                            "UPDATE timesheets_timesheet SET created_at = %s, updated_at = %s "
                            "WHERE id = %s",
                            [data['created_at'], data['updated_at'], timesheet.id]
                        )
                    else:
                        # Sauvegarder normalement avec validation
                        timesheet.save()

                    # Appeler la logique de correspondance de planning
                    from timesheets.views import TimesheetCreateView
                    from django.utils import timezone
                    view = TimesheetCreateView()
                    local_timestamp = timezone.localtime(timesheet.timestamp)

                    # Afficher les informations détaillées sur le pointage
                    self.stdout.write(f"Appel de _match_schedule_and_check_anomalies pour {timesheet.site.nfc_id} {timesheet.employee.get_full_name()} - "
                                     f"{timesheet.timestamp} (heure locale: {local_timestamp}) - {timesheet.get_entry_type_display()}")

                    # Rechercher les plannings disponibles pour cet employé sur ce site
                    from sites.models import SiteEmployee, Schedule, ScheduleDetail
                    site_employee_relations = SiteEmployee.objects.filter(
                        site=timesheet.site,
                        employee=timesheet.employee,
                        is_active=True
                    ).select_related('schedule')

                    # Afficher les plannings disponibles
                    self.stdout.write(f"  Plannings disponibles pour cet employé sur ce site: {site_employee_relations.count()}")
                    for site_employee in site_employee_relations:
                        if site_employee.schedule and site_employee.schedule.is_active:
                            schedule = site_employee.schedule
                            self.stdout.write(f"  - Planning {schedule.id}: Type {schedule.schedule_type}")

                            # Vérifier si le planning a des détails pour ce jour
                            current_weekday = local_timestamp.weekday()
                            try:
                                schedule_detail = ScheduleDetail.objects.get(
                                    schedule=schedule,
                                    day_of_week=current_weekday
                                )

                                if schedule.schedule_type == 'FIXED':
                                    self.stdout.write(f"    Horaires pour {schedule_detail.get_day_of_week_display()} (jour {current_weekday}):")
                                    if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                                        self.stdout.write(f"    Matin: {schedule_detail.start_time_1}-{schedule_detail.end_time_1}")
                                    if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                                        self.stdout.write(f"    Après-midi: {schedule_detail.start_time_2}-{schedule_detail.end_time_2}")
                                    self.stdout.write(f"    Marges: Retard={schedule.late_arrival_margin or timesheet.site.late_margin} min, "
                                                   f"Départ anticipé={schedule.early_departure_margin or timesheet.site.early_departure_margin} min")
                                elif schedule.schedule_type == 'FREQUENCY':
                                    self.stdout.write(f"    Fréquence pour {schedule_detail.get_day_of_week_display()}: {schedule_detail.frequency_duration} minutes")
                                    self.stdout.write(f"    Tolérance: {schedule.frequency_tolerance_percentage or timesheet.site.frequency_tolerance}%")
                            except ScheduleDetail.DoesNotExist:
                                self.stdout.write(f"    Pas de détails pour le jour {current_weekday}")

                    # Exécuter la correspondance de planning
                    logger.debug(f"Avant appel de _match_schedule_and_check_anomalies: timesheet.id={timesheet.id}, is_late={timesheet.is_late}, late_minutes={timesheet.late_minutes}")
                    is_ambiguous = view._match_schedule_and_check_anomalies(timesheet)
                    logger.debug(f"Après appel de _match_schedule_and_check_anomalies: timesheet.id={timesheet.id}, is_late={timesheet.is_late}, late_minutes={timesheet.late_minutes}")

                    # Afficher les résultats détaillés
                    self.stdout.write(f"Résultat: is_ambiguous={is_ambiguous}, is_late={timesheet.is_late}, "
                                     f"late_minutes={timesheet.late_minutes}, is_early_departure={timesheet.is_early_departure}, "
                                     f"early_departure_minutes={timesheet.early_departure_minutes}, "
                                     f"is_out_of_schedule={timesheet.is_out_of_schedule}")

                    # Vérifier spécifiquement les retards pour User03
                    if timesheet.employee.get_full_name() == "N03 User03" and timesheet.is_late:
                        self.stdout.write(self.style.WARNING(f"Détection de retard pour User03: late_minutes={timesheet.late_minutes}"))
                        # Vérifier les anomalies existantes pour ce pointage
                        anomalies = Anomaly.objects.filter(timesheet=timesheet, anomaly_type=Anomaly.AnomalyType.LATE)
                        self.stdout.write(f"Nombre d'anomalies de retard pour ce pointage: {anomalies.count()}")
                        for anomaly in anomalies:
                            self.stdout.write(f"  - Anomalie ID: {anomaly.id}, Status: {anomaly.status}, Description: {anomaly.description}")

                    # Mettre à jour le statut du pointage
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
                    self.stdout.write(f"Pointage recréé: {timesheet.timestamp} - {timesheet.get_entry_type_display()}")

                except Exception as e:
                    error_count += 1
                    error_message = str(e)
                    self.stdout.write(self.style.ERROR(f"Erreur lors de la recréation du pointage: {error_message}"))

                    # Si l'option ignore-errors n'est pas activée, lever l'exception
                    if not self.ignore_errors:
                        raise

        finally:
            # Restaurer les récepteurs
            pre_save.receivers = saved_pre_save_receivers
            post_save.receivers = saved_post_save_receivers

        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"{error_count} erreurs rencontrées lors de la recréation des pointages"))

        return processed_count

    def _recalculate_timesheet_status(self, start_date, end_date, site_id=None, employee_id=None, dry_run=False):
        """Recalcule le statut de tous les pointages dans la période spécifiée"""
        # Configurer le logger
        logger = logging.getLogger(__name__)

        query = Timesheet.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

        if site_id:
            query = query.filter(site_id=site_id)

        if employee_id:
            query = query.filter(employee_id=employee_id)

        # Ordonner les pointages par timestamp croissant (du plus ancien au plus récent)
        # pour traiter les arrivées avant les départs
        query = query.order_by('timestamp')

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
                    from django.utils import timezone
                    view = TimesheetCreateView()
                    local_timestamp = timezone.localtime(timesheet.timestamp)

                    # Afficher les informations détaillées sur le pointage
                    self.stdout.write(f"Appel de _match_schedule_and_check_anomalies pour {timesheet.site.nfc_id} {timesheet.employee.get_full_name()} - "
                                     f"{timesheet.timestamp} (heure locale: {local_timestamp}) - {timesheet.get_entry_type_display()}")

                    # Rechercher les plannings disponibles pour cet employé sur ce site
                    from sites.models import SiteEmployee, Schedule, ScheduleDetail
                    site_employee_relations = SiteEmployee.objects.filter(
                        site=timesheet.site,
                        employee=timesheet.employee,
                        is_active=True
                    ).select_related('schedule')

                    # Afficher les plannings disponibles
                    self.stdout.write(f"  Plannings disponibles pour cet employé sur ce site: {site_employee_relations.count()}")
                    for site_employee in site_employee_relations:
                        if site_employee.schedule and site_employee.schedule.is_active:
                            schedule = site_employee.schedule
                            self.stdout.write(f"  - Planning {schedule.id}: Type {schedule.schedule_type}")

                            # Vérifier si le planning a des détails pour ce jour
                            current_weekday = local_timestamp.weekday()
                            try:
                                schedule_detail = ScheduleDetail.objects.get(
                                    schedule=schedule,
                                    day_of_week=current_weekday
                                )

                                if schedule.schedule_type == 'FIXED':
                                    self.stdout.write(f"    Horaires pour {schedule_detail.get_day_of_week_display()} (jour {current_weekday}):")
                                    if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                                        self.stdout.write(f"    Matin: {schedule_detail.start_time_1}-{schedule_detail.end_time_1}")
                                    if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                                        self.stdout.write(f"    Après-midi: {schedule_detail.start_time_2}-{schedule_detail.end_time_2}")
                                    self.stdout.write(f"    Marges: Retard={schedule.late_arrival_margin or timesheet.site.late_margin} min, "
                                                   f"Départ anticipé={schedule.early_departure_margin or timesheet.site.early_departure_margin} min")
                                elif schedule.schedule_type == 'FREQUENCY':
                                    self.stdout.write(f"    Fréquence pour {schedule_detail.get_day_of_week_display()}: {schedule_detail.frequency_duration} minutes")
                                    self.stdout.write(f"    Tolérance: {schedule.frequency_tolerance_percentage or timesheet.site.frequency_tolerance}%")
                            except ScheduleDetail.DoesNotExist:
                                self.stdout.write(f"    Pas de détails pour le jour {current_weekday}")

                    # Exécuter la correspondance de planning
                    logger.debug(f"Avant appel de _match_schedule_and_check_anomalies: timesheet.id={timesheet.id}, is_late={timesheet.is_late}, late_minutes={timesheet.late_minutes}")
                    is_ambiguous = view._match_schedule_and_check_anomalies(timesheet)
                    logger.debug(f"Après appel de _match_schedule_and_check_anomalies: timesheet.id={timesheet.id}, is_late={timesheet.is_late}, late_minutes={timesheet.late_minutes}")

                    # Afficher les résultats détaillés
                    self.stdout.write(f"Résultat: is_ambiguous={timesheet.is_ambiguous}, is_late={timesheet.is_late}, "
                                     f"late_minutes={timesheet.late_minutes}, is_early_departure={timesheet.is_early_departure}, "
                                     f"early_departure_minutes={timesheet.early_departure_minutes}, "
                                     f"is_out_of_schedule={timesheet.is_out_of_schedule}")

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


