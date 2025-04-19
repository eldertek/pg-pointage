import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from timesheets.models import Timesheet, Anomaly
from sites.models import Site, SiteEmployee, Schedule, ScheduleDetail
from users.models import User
from core.utils import is_entity_active


class Command(BaseCommand):
    help = '''
    Vérifie les pointages manquants pour tous les employés ayant un planning actif.
    Crée des anomalies pour les employés qui n'ont pas pointé selon leur planning.

    Exemples d'utilisation :

    # Vérifier les pointages manquants pour aujourd'hui
    python manage.py check_missed_checkins

    # Vérifier les pointages manquants pour une date spécifique
    python manage.py check_missed_checkins --date 2023-04-01

    # Vérifier les pointages manquants pour un site spécifique
    python manage.py check_missed_checkins --site 1

    # Vérifier les pointages manquants pour un employé spécifique
    python manage.py check_missed_checkins --employee 1

    # Exécuter en mode simulation sans modifier la base de données
    python manage.py check_missed_checkins --dry-run

    # Afficher des informations détaillées pendant l'exécution
    python manage.py check_missed_checkins --verbose
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
            help='Date au format YYYY-MM-DD (par défaut: aujourd\'hui)'
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
        self.verbose = options['verbose']

        # Définir la date à vérifier
        check_date = options['date'] or timezone.now().date()

        # Filtrer par site si spécifié
        site_id = options['site']
        site = None
        if site_id:
            try:
                site = Site.objects.get(pk=site_id)
                self.stdout.write(f"Site: {site.name} (ID: {site.id})")
            except Site.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Site avec ID {site_id} non trouvé"))
                return

        # Filtrer par employé si spécifié
        employee_id = options['employee']
        employee = None
        if employee_id:
            try:
                employee = User.objects.get(pk=employee_id)
                self.stdout.write(f"Employé: {employee.get_full_name()} (ID: {employee.id})")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Employé avec ID {employee_id} non trouvé"))
                return

        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode simulation activé - aucune modification ne sera effectuée"))

        self.stdout.write(f"Vérification des pointages manquants pour le {check_date}")

        # Commencer la vérification
        try:
            # Utiliser une transaction seulement si on n'est pas en mode simulation
            if dry_run:
                self._check_missed_checkins(check_date, site, employee, dry_run)
            else:
                with transaction.atomic():
                    self._check_missed_checkins(check_date, site, employee, dry_run)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la vérification des pointages manquants: {str(e)}"))
            raise

    def _check_missed_checkins(self, check_date, site=None, employee=None, dry_run=False):
        # Récupérer toutes les relations site-employé actives
        site_employees = SiteEmployee.objects.filter(is_active=True).select_related('site', 'employee', 'schedule')

        # Filtrer par site si spécifié
        if site:
            site_employees = site_employees.filter(site=site)

        # Filtrer par employé si spécifié
        if employee:
            site_employees = site_employees.filter(employee=employee)

        # Compter les anomalies créées
        anomalies_created = 0

        # Pour chaque relation site-employé
        for site_employee in site_employees:
            # Vérifier si le site est actif
            if not is_entity_active(site_employee.site):
                if self.verbose:
                    self.stdout.write(f"Site {site_employee.site.name} inactif ou hors période d'activation pour {site_employee.employee.get_full_name()}")
                continue

            # Vérifier si l'employé est actif
            if not is_entity_active(site_employee.employee):
                if self.verbose:
                    self.stdout.write(f"Employé {site_employee.employee.get_full_name()} inactif ou hors période d'activation au site {site_employee.site.name}")
                continue

            # Vérifier si l'employé a un planning actif
            schedule = site_employee.schedule
            if not schedule or not is_entity_active(schedule):
                if self.verbose:
                    self.stdout.write(f"Pas de planning actif pour {site_employee.employee.get_full_name()} au site {site_employee.site.name}")
                continue

            # Vérifier si le planning a des détails pour ce jour de la semaine
            day_of_week = check_date.weekday()  # 0 = Lundi, 6 = Dimanche
            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=day_of_week
                )
            except ScheduleDetail.DoesNotExist:
                if self.verbose:
                    self.stdout.write(f"Pas de détails de planning pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le jour {day_of_week}")
                continue

            # Pour les plannings fixes, vérifier si l'employé a pointé
            if schedule.schedule_type == Schedule.ScheduleType.FIXED:
                # Récupérer tous les pointages de l'employé pour ce jour
                timesheets = Timesheet.objects.filter(
                    employee=site_employee.employee,
                    site=site_employee.site,
                    timestamp__date=check_date
                )

                # Compter les arrivées et départs
                arrivals = timesheets.filter(entry_type=Timesheet.EntryType.ARRIVAL).count()
                departures = timesheets.filter(entry_type=Timesheet.EntryType.DEPARTURE).count()
                total_entries = arrivals + departures

                # Déterminer si c'est un planning journalier ou demi-journée
                is_full_day = schedule_detail.start_time_1 and schedule_detail.end_time_1 and schedule_detail.start_time_2 and schedule_detail.end_time_2
                is_half_day = (schedule_detail.start_time_1 and schedule_detail.end_time_1 and not schedule_detail.start_time_2) or \
                              (not schedule_detail.start_time_1 and schedule_detail.start_time_2 and schedule_detail.end_time_2)

                if self.verbose:
                    self.stdout.write(f"Pointages pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}: "
                                     f"{arrivals} arrivées, {departures} départs, {total_entries} total")
                    self.stdout.write(f"Type de journée: {'Journée complète' if is_full_day else 'Demi-journée' if is_half_day else 'Indéterminé'}")

                # Vérifier les arrivées manquantes
                if arrivals == 0 and (schedule_detail.start_time_1 or schedule_detail.start_time_2):
                    # Vérifier si une anomalie similaire existe déjà
                    existing_anomaly = Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
                    ).first()

                    if not existing_anomaly and not dry_run:
                        # Créer une anomalie pour l'arrivée manquante
                        description = f"Arrivée manquante selon le planning"
                        if schedule_detail.start_time_1:
                            description += f" (heure prévue: {schedule_detail.start_time_1})"
                        elif schedule_detail.start_time_2:
                            description += f" (heure prévue: {schedule_detail.start_time_2})"

                        anomaly = Anomaly.objects.create(
                            employee=site_employee.employee,
                            site=site_employee.site,
                            date=check_date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                            description=description,
                            status=Anomaly.AnomalyStatus.PENDING,
                            schedule=schedule
                        )

                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie créée: MISSING_ARRIVAL - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                    elif existing_anomaly:
                        if self.verbose:
                            self.stdout.write(f"Anomalie existante pour arrivée manquante de {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: MISSING_ARRIVAL - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))

                # Vérifier les départs manquants
                if departures < arrivals and (schedule_detail.end_time_1 or schedule_detail.end_time_2):
                    # Vérifier si une anomalie similaire existe déjà
                    existing_anomaly = Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
                    ).first()

                    if not existing_anomaly and not dry_run:
                        # Créer une anomalie pour le départ manquant
                        description = f"Départ manquant selon le planning"
                        if schedule_detail.end_time_1 and not schedule_detail.end_time_2:
                            description += f" (heure prévue: {schedule_detail.end_time_1})"
                        elif schedule_detail.end_time_2:
                            description += f" (heure prévue: {schedule_detail.end_time_2})"

                        anomaly = Anomaly.objects.create(
                            employee=site_employee.employee,
                            site=site_employee.site,
                            date=check_date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
                            description=description,
                            status=Anomaly.AnomalyStatus.PENDING,
                            schedule=schedule
                        )

                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie créée: MISSING_DEPARTURE - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                    elif existing_anomaly:
                        if self.verbose:
                            self.stdout.write(f"Anomalie existante pour départ manquant de {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: MISSING_DEPARTURE - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))

                # Vérifier le nombre total de pointages selon le type de journée
                expected_entries = 4 if is_full_day else 2 if is_half_day else 0
                if expected_entries > 0 and total_entries < expected_entries and total_entries > 0:
                    # Vérifier si une anomalie similaire existe déjà
                    existing_anomaly = Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
                    ).first() or Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
                    ).first()

                    if not existing_anomaly and not dry_run:
                        # Créer une anomalie pour pointage manquant
                        description = f"Pointage manquant selon le planning ({total_entries}/{expected_entries})"

                        anomaly = Anomaly.objects.create(
                            employee=site_employee.employee,
                            site=site_employee.site,
                            date=check_date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL if arrivals < (expected_entries // 2) else Anomaly.AnomalyType.MISSING_DEPARTURE,
                            description=description,
                            status=Anomaly.AnomalyStatus.PENDING,
                            schedule=schedule
                        )

                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie créée: Pointage manquant - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                    elif existing_anomaly:
                        if self.verbose:
                            self.stdout.write(f"Anomalie existante pour pointage manquant de {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: Pointage manquant - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))

            # Pour les plannings fréquence, la logique est différente
            # On vérifie le nombre de pointages dans la journée
            elif schedule.schedule_type == Schedule.ScheduleType.FREQUENCY:
                # Récupérer tous les pointages de l'employé pour ce jour
                timesheets = Timesheet.objects.filter(
                    employee=site_employee.employee,
                    site=site_employee.site,
                    timestamp__date=check_date
                )

                # Compter les arrivées et départs
                arrivals = timesheets.filter(entry_type=Timesheet.EntryType.ARRIVAL).count()
                departures = timesheets.filter(entry_type=Timesheet.EntryType.DEPARTURE).count()
                total_entries = arrivals + departures

                if self.verbose:
                    self.stdout.write(f"Pointages pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date} (fréquence): "
                                     f"{arrivals} arrivées, {departures} départs, {total_entries} total")

                # Si l'employé n'a pas pointé du tout et qu'il devrait avoir un planning ce jour-là
                if total_entries == 0 and schedule_detail.frequency_duration:
                    # Vérifier si une anomalie similaire existe déjà
                    existing_anomaly = Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
                    ).first()

                    if not existing_anomaly and not dry_run:
                        # Créer une anomalie pour le passage manqué
                        description = f"Passage manqué selon le planning fréquence (durée prévue: {schedule_detail.frequency_duration} minutes)"

                        anomaly = Anomaly.objects.create(
                            employee=site_employee.employee,
                            site=site_employee.site,
                            date=check_date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                            description=description,
                            status=Anomaly.AnomalyStatus.PENDING,
                            schedule=schedule
                        )

                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie créée: MISSING_ARRIVAL - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                    elif existing_anomaly:
                        if self.verbose:
                            self.stdout.write(f"Anomalie existante pour passage manqué de {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: MISSING_ARRIVAL - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                # Si l'employé a pointé une seule fois (arrivée sans départ ou départ sans arrivée)
                elif total_entries == 1 and schedule_detail.frequency_duration:
                    # Vérifier si une anomalie similaire existe déjà
                    existing_anomaly = Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE if arrivals > departures else Anomaly.AnomalyType.MISSING_ARRIVAL
                    ).first()

                    if not existing_anomaly and not dry_run:
                        # Créer une anomalie pour le pointage manquant
                        anomaly_type = Anomaly.AnomalyType.MISSING_DEPARTURE if arrivals > departures else Anomaly.AnomalyType.MISSING_ARRIVAL
                        description = f"Pointage manquant selon le planning fréquence (durée prévue: {schedule_detail.frequency_duration} minutes)"

                        anomaly = Anomaly.objects.create(
                            employee=site_employee.employee,
                            site=site_employee.site,
                            date=check_date,
                            anomaly_type=anomaly_type,
                            description=description,
                            status=Anomaly.AnomalyStatus.PENDING,
                            schedule=schedule
                        )

                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie créée: {anomaly_type} - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                    elif existing_anomaly:
                        if self.verbose:
                            self.stdout.write(f"Anomalie existante pour pointage manquant de {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        anomaly_type = Anomaly.AnomalyType.MISSING_DEPARTURE if arrivals > departures else Anomaly.AnomalyType.MISSING_ARRIVAL
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: {anomaly_type} - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                # Si l'employé a pointé au moins 2 fois, c'est déjà traité dans le scan
                elif total_entries >= 2:
                    if self.verbose:
                        self.stdout.write(f"{site_employee.employee.get_full_name()} a pointé {total_entries} fois au site {site_employee.site.name} le {check_date} (déjà traité dans le scan)")

        self.stdout.write(self.style.SUCCESS(f"{anomalies_created} anomalies créées pour les pointages manquants"))
