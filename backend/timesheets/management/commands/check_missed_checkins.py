import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from timesheets.models import Timesheet, Anomaly
from sites.models import Site, SiteEmployee, Schedule, ScheduleDetail
from users.models import User


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
            # Vérifier si l'employé a un planning actif
            schedule = site_employee.schedule
            if not schedule or not schedule.is_active:
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
                # Vérifier si l'employé a pointé son arrivée ce jour-là
                has_arrival = Timesheet.objects.filter(
                    employee=site_employee.employee,
                    site=site_employee.site,
                    timestamp__date=check_date,
                    entry_type=Timesheet.EntryType.ARRIVAL
                ).exists()
                
                # Si l'employé n'a pas pointé son arrivée et qu'il devrait avoir un planning ce jour-là
                if not has_arrival and (schedule_detail.start_time_1 or schedule_detail.start_time_2):
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
                            self.stdout.write(f"Anomalie existante pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: MISSING_ARRIVAL - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                elif has_arrival:
                    if self.verbose:
                        self.stdout.write(f"{site_employee.employee.get_full_name()} a déjà pointé son arrivée au site {site_employee.site.name} le {check_date}")
            
            # Pour les plannings fréquence, la logique est différente
            # On vérifie si l'employé a pointé au moins une fois dans la journée
            elif schedule.schedule_type == Schedule.ScheduleType.FREQUENCY:
                # Vérifier si l'employé a pointé au moins une fois ce jour-là
                has_timesheet = Timesheet.objects.filter(
                    employee=site_employee.employee,
                    site=site_employee.site,
                    timestamp__date=check_date
                ).exists()
                
                # Si l'employé n'a pas pointé du tout et qu'il devrait avoir un planning ce jour-là
                if not has_timesheet and schedule_detail.frequency_duration:
                    # Vérifier si une anomalie similaire existe déjà
                    existing_anomaly = Anomaly.objects.filter(
                        employee=site_employee.employee,
                        site=site_employee.site,
                        date=check_date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
                    ).first()
                    
                    if not existing_anomaly and not dry_run:
                        # Créer une anomalie pour l'arrivée manquante
                        description = f"Pointage manquant selon le planning fréquence (durée prévue: {schedule_detail.frequency_duration} minutes)"
                        
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
                            self.stdout.write(f"Anomalie existante pour {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}")
                    elif dry_run:
                        # En mode simulation, on compte quand même l'anomalie
                        anomalies_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"Anomalie simulée: MISSING_ARRIVAL - {site_employee.employee.get_full_name()} au site {site_employee.site.name} le {check_date}"
                        ))
                elif has_timesheet:
                    if self.verbose:
                        self.stdout.write(f"{site_employee.employee.get_full_name()} a déjà pointé au site {site_employee.site.name} le {check_date}")
        
        self.stdout.write(self.style.SUCCESS(f"{anomalies_created} anomalies créées pour les pointages manquants"))
