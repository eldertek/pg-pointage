import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from core.utils import is_entity_active

User = get_user_model()

class Command(BaseCommand):
    help = '''
    Vérifie les pointages manquants en temps réel pour tous les employés ayant un planning actif.
    Cette commande est conçue pour être exécutée toutes les minutes via un cron job.
    Elle suit l'arbre de décision défini dans .cursor/rules/minute_anomalies.mdc.

    Exemples d'utilisation :

    # Vérifier les pointages manquants en temps réel
    python manage.py check_minute_anomalies

    # Vérifier les pointages manquants pour un site spécifique
    python manage.py check_minute_anomalies --site 1

    # Vérifier les pointages manquants pour un employé spécifique
    python manage.py check_minute_anomalies --employee 1

    # Exécuter en mode simulation sans modifier la base de données
    python manage.py check_minute_anomalies --dry-run

    # Afficher des informations détaillées pendant l'exécution
    python manage.py check_minute_anomalies --verbose
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.verbose = False
        self.day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            type=int,
            help='ID du site pour lequel vérifier les pointages manquants'
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='ID de l\'employé pour lequel vérifier les pointages manquants'
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
        # Configurer le mode verbose
        self.verbose = options.get('verbose', False)
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
            self.stdout.write("Mode verbose activé")

        # Récupérer les options
        site_id = options.get('site')
        employee_id = options.get('employee')
        dry_run = options.get('dry_run', False)

        # Récupérer le site et l'employé si spécifiés
        site = None
        employee = None

        if site_id:
            try:
                site = Site.objects.get(id=site_id)
                self.stdout.write(f"Site spécifié: {site.name} (ID: {site_id})")
            except Site.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Site avec ID {site_id} non trouvé"))
                return

        if employee_id:
            try:
                employee = User.objects.get(id=employee_id)
                self.stdout.write(f"Employé spécifié: {employee.get_full_name()} (ID: {employee_id})")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Employé avec ID {employee_id} non trouvé"))
                return

        # Heure actuelle
        current_time = timezone.now()
        self.stdout.write(f"Vérification des pointages manquants à {current_time.strftime('%H:%M:%S')}")

        # Commencer la vérification
        try:
            # Utiliser une transaction seulement si on n'est pas en mode simulation
            if dry_run:
                anomalies_created = self._check_minute_anomalies(current_time, site, employee, dry_run)
            else:
                with transaction.atomic():
                    anomalies_created = self._check_minute_anomalies(current_time, site, employee, dry_run)

            self.stdout.write(self.style.SUCCESS(f"Vérification terminée: {anomalies_created} anomalies créées"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la vérification des pointages manquants: {str(e)}"))
            raise

    def _check_minute_anomalies(self, current_time, site=None, employee=None, dry_run=False):
        """
        Vérifie les pointages manquants en temps réel selon l'arbre de décision.
        Suit la logique définie dans .cursor/rules/minute_anomalies.mdc
        """
        # Récupérer toutes les relations site-employé actives
        site_employees = SiteEmployee.objects.filter(is_active=True).select_related('site', 'employee', 'schedule')

        # Filtrer par site si spécifié
        if site:
            site_employees = site_employees.filter(site=site)

        # Filtrer par employé si spécifié
        if employee:
            site_employees = site_employees.filter(employee=employee)

        # Date actuelle
        current_date = current_time.date()
        current_weekday = current_date.weekday()
        current_time_obj = current_time.time()

        # Compter les anomalies créées
        anomalies_created = 0

        # Parcourir toutes les relations site-employé
        for site_employee in site_employees:
            # Vérifier si le site est actif
            if not is_entity_active(site_employee.site):
                if self.verbose:
                    self.stdout.write(f"Site {site_employee.site.name} inactif ou hors période d'activation, ignoré")
                continue

            # Vérifier si l'employé est actif
            if not is_entity_active(site_employee.employee):
                if self.verbose:
                    self.stdout.write(f"Employé {site_employee.employee.get_full_name()} inactif ou hors période d'activation, ignoré")
                continue

            # Récupérer le planning
            schedule = site_employee.schedule
            if not schedule or not is_entity_active(schedule):
                if self.verbose:
                    self.stdout.write(f"Planning inactif ou non défini pour {site_employee.employee.get_full_name()} au site {site_employee.site.name}, ignoré")
                continue

            # Vérifier si le planning a des détails pour ce jour
            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=current_weekday
                )
            except ScheduleDetail.DoesNotExist:
                if self.verbose:
                    self.stdout.write(f"Pas de planning défini pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {self.day_names[current_weekday]}, ignoré")
                continue

            # Vérifier le type de planning
            if schedule.schedule_type == Schedule.ScheduleType.FIXED:
                # Récupérer les pointages de l'employé pour aujourd'hui
                timesheets = Timesheet.objects.filter(
                    employee=site_employee.employee,
                    site=site_employee.site,
                    timestamp__date=current_date
                ).order_by('timestamp')

                # Compter les pointages
                timesheet_count = timesheets.count()

                # Récupérer la marge de retard
                late_margin = schedule.late_arrival_margin or site_employee.site.late_margin or 15  # Valeur par défaut: 15 minutes

                # Vérifier selon le type de journée et le nombre de pointages
                day_type = schedule_detail.day_type

                # Cas 1: Planning journalier
                if day_type == ScheduleDetail.DayType.FULL:
                    # Cas 1.1: Aucun pointage
                    if timesheet_count == 0:
                        # Vérifier si l'heure actuelle dépasse l'heure d'arrivée du matin + marge
                        if schedule_detail.start_time_1 and current_time_obj > self._add_minutes_to_time(schedule_detail.start_time_1, late_margin):
                            # Créer une anomalie pour pointage manquant
                            if not dry_run:
                                self._create_missing_arrival_anomaly(site_employee, schedule, current_date)
                                anomalies_created += 1
                            if self.verbose:
                                self.stdout.write(self.style.WARNING(
                                    f"Anomalie détectée: Pointage manquant pour {site_employee.employee.get_full_name()} "
                                    f"au site {site_employee.site.name} le {current_date} (heure actuelle: {current_time_obj}, "
                                    f"heure d'arrivée prévue: {schedule_detail.start_time_1})"
                                ))

                    # Cas 1.2: Deux pointages (après-midi)
                    elif timesheet_count == 2:
                        # Vérifier si l'heure actuelle dépasse l'heure d'arrivée de l'après-midi + marge
                        if schedule_detail.start_time_2 and current_time_obj > self._add_minutes_to_time(schedule_detail.start_time_2, late_margin):
                            # Créer une anomalie pour pointage manquant
                            if not dry_run:
                                self._create_missing_arrival_anomaly(site_employee, schedule, current_date)
                                anomalies_created += 1
                            if self.verbose:
                                self.stdout.write(self.style.WARNING(
                                    f"Anomalie détectée: Pointage manquant pour {site_employee.employee.get_full_name()} "
                                    f"au site {site_employee.site.name} le {current_date} (heure actuelle: {current_time_obj}, "
                                    f"heure d'arrivée après-midi prévue: {schedule_detail.start_time_2})"
                                ))

                # Cas 2: Planning demi-journée (matin ou après-midi)
                elif day_type in [ScheduleDetail.DayType.AM, ScheduleDetail.DayType.PM]:
                    # Cas 2.1: Aucun pointage
                    if timesheet_count == 0:
                        # Déterminer l'heure d'arrivée selon le type de demi-journée
                        arrival_time = None
                        if day_type == ScheduleDetail.DayType.AM and schedule_detail.start_time_1:
                            arrival_time = schedule_detail.start_time_1
                        elif day_type == ScheduleDetail.DayType.PM and schedule_detail.start_time_2:
                            arrival_time = schedule_detail.start_time_2

                        # Vérifier si l'heure actuelle dépasse l'heure d'arrivée + marge
                        if arrival_time and current_time_obj > self._add_minutes_to_time(arrival_time, late_margin):
                            # Créer une anomalie pour pointage manquant
                            if not dry_run:
                                self._create_missing_arrival_anomaly(site_employee, schedule, current_date)
                                anomalies_created += 1
                            if self.verbose:
                                self.stdout.write(self.style.WARNING(
                                    f"Anomalie détectée: Pointage manquant pour {site_employee.employee.get_full_name()} "
                                    f"au site {site_employee.site.name} le {current_date} (heure actuelle: {current_time_obj}, "
                                    f"heure d'arrivée prévue: {arrival_time})"
                                ))

            # Pour les plannings de type fréquence, aucune anomalie n'est générée ici
            # selon l'arbre de décision dans minute_anomalies.mdc

        return anomalies_created

    def _add_minutes_to_time(self, time_obj, minutes):
        """Ajoute des minutes à un objet time"""
        datetime_obj = datetime.combine(datetime.today(), time_obj)
        datetime_obj += timedelta(minutes=minutes)
        return datetime_obj.time()

    def _create_missing_arrival_anomaly(self, site_employee, schedule, date):
        """Crée une anomalie pour un pointage d'arrivée manquant"""
        # Vérifier si une anomalie similaire existe déjà pour cette date/employé/site
        existing_anomaly = Anomaly.objects.filter(
            employee=site_employee.employee,
            site=site_employee.site,
            date=date,
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
            status=Anomaly.AnomalyStatus.PENDING
        ).first()

        if not existing_anomaly:
            # Créer une anomalie pour pointage manquant
            description = f"Pointage d'arrivée manquant détecté en temps réel"

            anomaly = Anomaly.objects.create(
                employee=site_employee.employee,
                site=site_employee.site,
                date=date,
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                description=description,
                status=Anomaly.AnomalyStatus.PENDING,
                schedule=schedule
            )

            self.stdout.write(self.style.SUCCESS(
                f"Anomalie créée: Pointage d'arrivée manquant - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {date}"
            ))
            return anomaly
        else:
            self.stdout.write(
                f"Anomalie existante pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {date}, pas de nouvelle anomalie créée"
            )
            return None
