from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, F, Prefetch
from datetime import datetime, timedelta
import pytz
from tabulate import tabulate

from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from users.models import User
from timesheets.models import Timesheet, Anomaly


class Command(BaseCommand):
    help = '''
    Affiche en une seule vue les plannings, employés rattachés, pointages et anomalies détectées.
    
    Exemples d'utilisation :
    
    # Afficher les données pour aujourd'hui
    python manage.py display_all_data
    
    # Afficher les données pour une date spécifique
    python manage.py display_all_data --date 2023-04-01
    
    # Afficher les données pour un site spécifique
    python manage.py display_all_data --site 1
    
    # Afficher les données pour un employé spécifique
    python manage.py display_all_data --employee 1
    
    # Afficher les données pour un planning spécifique
    python manage.py display_all_data --schedule 1
    
    # Afficher uniquement les données avec anomalies
    python manage.py display_all_data --anomalies-only
    
    # Afficher les données pour les 7 derniers jours
    python manage.py display_all_data --days 7
    '''
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
            help='Date pour laquelle afficher les données (format: YYYY-MM-DD)'
        )
        parser.add_argument(
            '--site',
            type=int,
            help='ID du site pour lequel afficher les données'
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='ID de l\'employé pour lequel afficher les données'
        )
        parser.add_argument(
            '--schedule',
            type=int,
            help='ID du planning pour lequel afficher les données'
        )
        parser.add_argument(
            '--anomalies-only',
            action='store_true',
            help='Afficher uniquement les données avec anomalies'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Nombre de jours à afficher (par défaut: 1 jour)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher des informations détaillées'
        )
    
    def handle(self, *args, **options):
        # Récupérer les paramètres
        self.verbose = options.get('verbose', False)
        date_param = options.get('date')
        site_id = options.get('site')
        employee_id = options.get('employee')
        schedule_id = options.get('schedule')
        anomalies_only = options.get('anomalies_only', False)
        days = options.get('days', 1)
        
        # Définir la période
        if date_param:
            start_date = date_param
            end_date = date_param
        else:
            # Utiliser la date actuelle
            today = timezone.localtime().date()
            start_date = today - timedelta(days=days-1)
            end_date = today
        
        self.stdout.write(f"Période: du {start_date} au {end_date}")
        
        # Construire les filtres
        schedule_filter = Q(is_active=True)
        if schedule_id:
            schedule_filter &= Q(id=schedule_id)
        
        site_filter = Q(is_active=True)
        if site_id:
            site_filter &= Q(id=site_id)
        
        employee_filter = Q(is_active=True)
        if employee_id:
            employee_filter &= Q(id=employee_id)
        
        # Récupérer les plannings
        schedules = Schedule.objects.filter(schedule_filter).select_related('site').prefetch_related(
            'details',
            Prefetch(
                'schedule_employees',
                queryset=SiteEmployee.objects.filter(is_active=True).select_related('employee'),
                to_attr='active_employees'
            )
        )
        
        if site_id:
            schedules = schedules.filter(site_id=site_id)
        
        # Préparer les données pour l'affichage
        all_data = []
        
        # Pour chaque planning
        for schedule in schedules:
            site = schedule.site
            
            # Récupérer les détails du planning
            for detail in schedule.details.all():
                # Pour chaque employé rattaché au planning
                for site_employee in schedule.active_employees:
                    employee = site_employee.employee
                    
                    # Appliquer le filtre d'employé si nécessaire
                    if employee_id and employee.id != employee_id:
                        continue
                    
                    # Récupérer les pointages de l'employé pour ce site dans la période
                    timesheets = Timesheet.objects.filter(
                        employee=employee,
                        site=site,
                        timestamp__date__range=[start_date, end_date]
                    ).order_by('timestamp')
                    
                    # Récupérer les anomalies de l'employé pour ce site dans la période
                    anomalies = Anomaly.objects.filter(
                        Q(employee=employee, site=site, date__range=[start_date, end_date]) |
                        Q(timesheet__employee=employee, timesheet__site=site, timesheet__timestamp__date__range=[start_date, end_date])
                    ).distinct()
                    
                    # Si on veut uniquement les données avec anomalies et qu'il n'y en a pas, passer
                    if anomalies_only and not anomalies.exists():
                        continue
                    
                    # Préparer les données de base
                    base_data = {
                        'Site': site.name,
                        'Planning ID': schedule.id,
                        'Type Planning': schedule.get_schedule_type_display(),
                        'Jour': detail.get_day_of_week_display(),
                        'Type Jour': detail.get_day_type_display() if hasattr(detail, 'get_day_type_display') else '',
                        'Horaires Matin': f"{detail.start_time_1}-{detail.end_time_1}" if detail.start_time_1 and detail.end_time_1 else '',
                        'Horaires Après-midi': f"{detail.start_time_2}-{detail.end_time_2}" if detail.start_time_2 and detail.end_time_2 else '',
                        'Durée Fréquence': f"{detail.frequency_duration} min" if detail.frequency_duration else '',
                        'Employé ID': employee.employee_id,
                        'Employé': f"{employee.first_name} {employee.last_name}",
                    }
                    
                    # Si aucun pointage ni anomalie, ajouter une ligne avec les données de base
                    if not timesheets.exists() and not anomalies.exists():
                        row_data = base_data.copy()
                        row_data.update({
                            'Pointage ID': '',
                            'Horodatage': '',
                            'Type Entrée': '',
                            'Retard': '',
                            'Départ Anticipé': '',
                            'Hors Planning': '',
                            'Anomalie ID': '',
                            'Type Anomalie': '',
                            'Statut Anomalie': '',
                            'Description': ''
                        })
                        all_data.append(row_data)
                    else:
                        # Pour chaque pointage
                        for timesheet in timesheets:
                            # Récupérer les anomalies liées à ce pointage
                            ts_anomalies = anomalies.filter(
                                Q(timesheet=timesheet) |
                                Q(related_timesheets=timesheet)
                            )
                            
                            # Si aucune anomalie liée, ajouter une ligne avec le pointage
                            if not ts_anomalies.exists():
                                row_data = base_data.copy()
                                row_data.update({
                                    'Pointage ID': timesheet.id,
                                    'Horodatage': timezone.localtime(timesheet.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                                    'Type Entrée': timesheet.get_entry_type_display(),
                                    'Retard': f"{timesheet.late_minutes} min" if timesheet.is_late else '',
                                    'Départ Anticipé': f"{timesheet.early_departure_minutes} min" if timesheet.is_early_departure else '',
                                    'Hors Planning': 'Oui' if timesheet.is_out_of_schedule else '',
                                    'Anomalie ID': '',
                                    'Type Anomalie': '',
                                    'Statut Anomalie': '',
                                    'Description': ''
                                })
                                all_data.append(row_data)
                            else:
                                # Pour chaque anomalie liée au pointage
                                for anomaly in ts_anomalies:
                                    row_data = base_data.copy()
                                    row_data.update({
                                        'Pointage ID': timesheet.id,
                                        'Horodatage': timezone.localtime(timesheet.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                                        'Type Entrée': timesheet.get_entry_type_display(),
                                        'Retard': f"{timesheet.late_minutes} min" if timesheet.is_late else '',
                                        'Départ Anticipé': f"{timesheet.early_departure_minutes} min" if timesheet.is_early_departure else '',
                                        'Hors Planning': 'Oui' if timesheet.is_out_of_schedule else '',
                                        'Anomalie ID': anomaly.id,
                                        'Type Anomalie': anomaly.get_anomaly_type_display(),
                                        'Statut Anomalie': anomaly.get_status_display(),
                                        'Description': anomaly.description[:50] + '...' if len(anomaly.description) > 50 else anomaly.description
                                    })
                                    all_data.append(row_data)
                        
                        # Ajouter les anomalies qui ne sont pas liées à un pointage
                        for anomaly in anomalies.filter(timesheet__isnull=True):
                            row_data = base_data.copy()
                            row_data.update({
                                'Pointage ID': '',
                                'Horodatage': '',
                                'Type Entrée': '',
                                'Retard': '',
                                'Départ Anticipé': '',
                                'Hors Planning': '',
                                'Anomalie ID': anomaly.id,
                                'Type Anomalie': anomaly.get_anomaly_type_display(),
                                'Statut Anomalie': anomaly.get_status_display(),
                                'Description': anomaly.description[:50] + '...' if len(anomaly.description) > 50 else anomaly.description
                            })
                            all_data.append(row_data)
        
        # Afficher les données
        if all_data:
            headers = {
                'Site': 'Site',
                'Planning ID': 'Planning ID',
                'Type Planning': 'Type Planning',
                'Jour': 'Jour',
                'Type Jour': 'Type Jour',
                'Horaires Matin': 'Horaires Matin',
                'Horaires Après-midi': 'Horaires Après-midi',
                'Durée Fréquence': 'Durée Fréquence',
                'Employé ID': 'Employé ID',
                'Employé': 'Employé',
                'Pointage ID': 'Pointage ID',
                'Horodatage': 'Horodatage',
                'Type Entrée': 'Type Entrée',
                'Retard': 'Retard',
                'Départ Anticipé': 'Départ Anticipé',
                'Hors Planning': 'Hors Planning',
                'Anomalie ID': 'Anomalie ID',
                'Type Anomalie': 'Type Anomalie',
                'Statut Anomalie': 'Statut Anomalie',
                'Description': 'Description'
            }
            
            # Convertir les données en liste pour tabulate
            table_data = []
            for row in all_data:
                table_row = [row.get(key, '') for key in headers.keys()]
                table_data.append(table_row)
            
            # Afficher le tableau
            self.stdout.write(tabulate(
                table_data,
                headers=headers.values(),
                tablefmt='grid'
            ))
            
            self.stdout.write(self.style.SUCCESS(f"{len(all_data)} lignes affichées"))
        else:
            self.stdout.write(self.style.WARNING("Aucune donnée trouvée pour les critères spécifiés"))
