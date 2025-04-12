import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, SiteEmployee, Schedule, ScheduleDetail
from users.models import User
from rest_framework.response import Response
from rest_framework import status

class AnomalyProcessor:
    """
    Classe utilitaire pour centraliser la logique de traitement des anomalies.
    Cette classe combine les meilleures pratiques de timesheets_repair.py, views.py et signals.py
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._anomalies_detected = False

    def _is_timesheet_matching_schedule(self, timesheet, schedule):
        """Vérifie si un pointage correspond à un planning"""
        if not schedule or not schedule.is_active:
            return False

        timestamp = timesheet.timestamp
        current_date = timestamp.date()
        current_weekday = current_date.weekday()
        current_time = timestamp.time()

        try:
            schedule_detail = ScheduleDetail.objects.get(
                schedule=schedule,
                day_of_week=current_weekday
            )

            if schedule.schedule_type == 'FIXED':
                # Vérifier les horaires du matin
                if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                    if schedule_detail.start_time_1 <= current_time <= schedule_detail.end_time_1:
                        return True

                # Vérifier les horaires de l'après-midi
                if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                    if schedule_detail.start_time_2 <= current_time <= schedule_detail.end_time_2:
                        return True

            elif schedule.schedule_type == 'FREQUENCY':
                return True

        except ScheduleDetail.DoesNotExist:
            return False

        return False

    def _find_employee_schedule(self, employee, site, date):
        """Trouve le planning associé à un employé et un site pour une date donnée."""
        site_employee_relations = SiteEmployee.objects.filter(
            site=site,
            employee=employee,
            is_active=True
        ).select_related('schedule')

        for site_employee in site_employee_relations:
            schedule = site_employee.schedule
            if not schedule or not schedule.is_active:
                continue

            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=date.weekday()
                )
                return schedule
            except ScheduleDetail.DoesNotExist:
                continue

        return None

    def _match_schedule_and_check_anomalies(self, timesheet):
        """Vérifie la correspondance avec le planning et crée les anomalies nécessaires"""
        employee = timesheet.employee
        site = timesheet.site
        entry_type = timesheet.entry_type
        timestamp = timesheet.timestamp
        local_timestamp = timezone.localtime(timestamp)
        current_date = local_timestamp.date()
        current_time = local_timestamp.time()

        self.logger.info(f"Vérification du planning pour: {employee.get_full_name()} ({employee.id}) - {site.name} ({site.id}) - "
                        f"{entry_type} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        site_employee_relations = SiteEmployee.objects.filter(
            site=site,
            employee=employee,
            is_active=True
        ).select_related('schedule')

        is_ambiguous = False
        is_out_of_schedule = True
        matched_schedule = None

        if not site_employee_relations.exists():
            timesheet.is_out_of_schedule = True
            timesheet.save()

            Anomaly.objects.create(
                employee=employee,
                site=site,
                timesheet=timesheet,
                date=current_date,
                anomaly_type=Anomaly.AnomalyType.OTHER,
                description=f"Pointage hors planning: l'employé n'est pas rattaché à ce site.",
                status=Anomaly.AnomalyStatus.PENDING
            )
            return True

        matching_schedules = []

        for site_employee in site_employee_relations:
            schedule = site_employee.schedule
            if not schedule or not schedule.is_active:
                continue

            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=current_date.weekday()
                )

                if schedule.schedule_type == Schedule.ScheduleType.FIXED:
                    is_matching = False

                    if current_time < timezone.datetime.strptime('07:30', '%H:%M').time() or \
                       current_time > timezone.datetime.strptime('19:00', '%H:%M').time():
                        is_out_of_schedule = True
                        continue

                    late_margin = schedule.late_arrival_margin or site.late_margin
                    early_departure_margin = schedule.early_departure_margin or site.early_departure_margin

                    if entry_type == Timesheet.EntryType.ARRIVAL:
                        if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                            if schedule_detail.start_time_1 <= current_time <= schedule_detail.end_time_1:
                                is_matching = True
                                if current_time > schedule_detail.start_time_1:
                                    late_minutes = int((datetime.combine(current_date, current_time) -
                                                    datetime.combine(current_date, schedule_detail.start_time_1)).total_seconds() / 60)

                                    if late_minutes > late_margin:
                                        timesheet.is_late = True
                                        timesheet.late_minutes = late_minutes
                                        self._create_late_anomaly(timesheet, late_minutes, late_margin, schedule)

                        if schedule_detail.start_time_2 and schedule_detail.end_time_2 and not is_matching:
                            if schedule_detail.start_time_2 <= current_time <= schedule_detail.end_time_2:
                                is_matching = True
                                if current_time > schedule_detail.start_time_2:
                                    late_minutes = int((datetime.combine(current_date, current_time) -
                                                    datetime.combine(current_date, schedule_detail.start_time_2)).total_seconds() / 60)

                                    if late_minutes > late_margin:
                                        timesheet.is_late = True
                                        timesheet.late_minutes = late_minutes
                                        self._create_late_anomaly(timesheet, late_minutes, late_margin, schedule)

                    elif entry_type == Timesheet.EntryType.DEPARTURE:
                        if schedule_detail.end_time_1 and current_time < schedule_detail.end_time_1:
                            is_matching = True
                            early_minutes = int((datetime.combine(current_date, schedule_detail.end_time_1) -
                                            datetime.combine(current_date, current_time)).total_seconds() / 60)

                            if early_minutes > early_departure_margin:
                                timesheet.is_early_departure = True
                                timesheet.early_departure_minutes = early_minutes
                                self._create_early_departure_anomaly(timesheet, early_minutes, early_departure_margin, schedule)

                        elif schedule_detail.end_time_2 and current_time < schedule_detail.end_time_2:
                            is_matching = True
                            early_minutes = int((datetime.combine(current_date, schedule_detail.end_time_2) -
                                            datetime.combine(current_date, current_time)).total_seconds() / 60)

                            if early_minutes > early_departure_margin:
                                timesheet.is_early_departure = True
                                timesheet.early_departure_minutes = early_minutes
                                self._create_early_departure_anomaly(timesheet, early_minutes, early_departure_margin, schedule)

                    if is_matching:
                        matching_schedules.append(schedule)
                        is_out_of_schedule = False
                        matched_schedule = schedule

                elif schedule.schedule_type == Schedule.ScheduleType.FREQUENCY:
                    matching_schedules.append(schedule)
                    is_out_of_schedule = False
                    matched_schedule = schedule

                    if entry_type == Timesheet.EntryType.DEPARTURE:
                        expected_duration = schedule_detail.frequency_duration
                        if expected_duration and expected_duration > 0:
                            tolerance_percentage = schedule.frequency_tolerance_percentage or site.frequency_tolerance or 10
                            min_duration = expected_duration * (1 - tolerance_percentage / 100)

                            last_arrival = Timesheet.objects.filter(
                                employee=employee,
                                site=site,
                                entry_type=Timesheet.EntryType.ARRIVAL,
                                timestamp__date=current_date,
                                timestamp__lt=timestamp
                            ).order_by('-timestamp').first()

                            if last_arrival:
                                duration_minutes = (timestamp - last_arrival.timestamp).total_seconds() / 60
                                if duration_minutes < min_duration:
                                    timesheet.is_early_departure = True
                                    timesheet.early_departure_minutes = int(min_duration - duration_minutes)

            except ScheduleDetail.DoesNotExist:
                continue

        if len(matching_schedules) > 1:
            is_ambiguous = True
            most_recent_schedule = max(matching_schedules, key=lambda s: s.created_at)
            matched_schedule = most_recent_schedule

        timesheet.is_out_of_schedule = is_out_of_schedule
        timesheet.is_ambiguous = is_ambiguous
        timesheet.save()

        if is_out_of_schedule:
            self._create_out_of_schedule_anomaly(timesheet)

        return is_ambiguous

    def _create_late_anomaly(self, timesheet, late_minutes, late_margin, schedule):
        """Crée une anomalie de retard"""
        existing_anomaly = Anomaly.objects.filter(
            employee=timesheet.employee,
            site=timesheet.site,
            date=timesheet.timestamp.date(),
            anomaly_type=Anomaly.AnomalyType.LATE,
            timesheet=timesheet
        ).first()

        if not existing_anomaly and late_minutes > late_margin:
            anomaly = Anomaly.objects.create(
                employee=timesheet.employee,
                site=timesheet.site,
                timesheet=timesheet,
                date=timesheet.timestamp.date(),
                anomaly_type=Anomaly.AnomalyType.LATE,
                description=f'Retard de {late_minutes} minutes.',
                minutes=late_minutes,
                status=Anomaly.AnomalyStatus.PENDING,
                schedule=schedule
            )
            anomaly.related_timesheets.add(timesheet)
            self._anomalies_detected = True

    def _create_early_departure_anomaly(self, timesheet, early_minutes, early_departure_margin, schedule):
        """Crée une anomalie de départ anticipé"""
        existing_anomaly = Anomaly.objects.filter(
            employee=timesheet.employee,
            site=timesheet.site,
            date=timesheet.timestamp.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
            timesheet=timesheet
        ).first()

        if not existing_anomaly and early_minutes > early_departure_margin:
            anomaly = Anomaly.objects.create(
                employee=timesheet.employee,
                site=timesheet.site,
                timesheet=timesheet,
                date=timesheet.timestamp.date(),
                anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                description=f'Départ anticipé de {early_minutes} minutes.',
                minutes=early_minutes,
                status=Anomaly.AnomalyStatus.PENDING,
                schedule=schedule
            )
            anomaly.related_timesheets.add(timesheet)
            self._anomalies_detected = True

    def _create_out_of_schedule_anomaly(self, timesheet):
        """Crée une anomalie de pointage hors planning"""
        existing_anomaly = Anomaly.objects.filter(
            employee=timesheet.employee,
            site=timesheet.site,
            date=timesheet.timestamp.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER,
            description__contains="Pointage hors planning"
        ).first()

        if not existing_anomaly:
            anomaly = Anomaly.objects.create(
                employee=timesheet.employee,
                site=timesheet.site,
                timesheet=timesheet,
                date=timesheet.timestamp.date(),
                anomaly_type=Anomaly.AnomalyType.OTHER,
                description="Pointage hors planning: aucun planning correspondant trouvé.",
                status=Anomaly.AnomalyStatus.PENDING
            )
            anomaly.related_timesheets.add(timesheet)
            self._anomalies_detected = True

    def process_timesheet(self, timesheet, force_update=False):
        """Traite un pointage individuel"""
        try:
            # Réinitialiser le flag d'anomalies détectées
            self._anomalies_detected = False

            if force_update:
                # Réinitialiser les statuts
                timesheet.is_late = False
                timesheet.late_minutes = 0
                timesheet.is_early_departure = False
                timesheet.early_departure_minutes = 0
                timesheet.is_out_of_schedule = False
                timesheet.is_ambiguous = False

            # Vérifier les anomalies
            is_ambiguous = self._match_schedule_and_check_anomalies(timesheet)

            return {
                'success': True,
                'message': 'Pointage traité avec succès',
                'is_ambiguous': is_ambiguous,
                'has_anomalies': self._anomalies_detected
            }

        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du pointage: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Erreur lors du traitement du pointage: {str(e)}"
            }

    def has_anomalies(self):
        """Retourne True si des anomalies ont été détectées lors du traitement"""
        return self._anomalies_detected

    def scan_anomalies(self, start_date=None, end_date=None, site_id=None, employee_id=None, force_update=False):
        """Scan complet des anomalies sur une période"""
        try:
            with transaction.atomic():
                # Définir la période par défaut si non spécifiée
                end_date = end_date or timezone.now().date()
                start_date = start_date or (end_date - timedelta(days=30))

                # Construire la requête de base
                timesheets = Timesheet.objects.filter(
                    timestamp__date__gte=start_date,
                    timestamp__date__lte=end_date
                ).order_by('timestamp')

                if site_id:
                    timesheets = timesheets.filter(site_id=site_id)
                if employee_id:
                    timesheets = timesheets.filter(employee_id=employee_id)

                # Si force_update est True, supprimer toutes les anomalies existantes
                if force_update:
                    anomalies_filter = Q(date__gte=start_date, date__lte=end_date)
                    if site_id:
                        anomalies_filter &= Q(site_id=site_id)
                    if employee_id:
                        anomalies_filter &= Q(employee_id=employee_id)

                    Anomaly.objects.filter(anomalies_filter).delete()

                    # Réinitialiser les statuts des pointages
                    for ts in timesheets:
                        ts.is_late = False
                        ts.late_minutes = 0
                        ts.is_early_departure = False
                        ts.early_departure_minutes = 0
                        ts.is_out_of_schedule = False
                        ts.is_ambiguous = False
                        ts.save()

                # Traiter chaque pointage
                anomalies_created = 0
                for timesheet in timesheets:
                    result = self.process_timesheet(timesheet, force_update=force_update)
                    if result['success'] and result.get('has_anomalies', False):
                        anomalies_created += 1

                return Response({
                    'message': f'{anomalies_created} anomalies traitées',
                    'anomalies_created': anomalies_created,
                    'force_update': force_update
                })

        except Exception as e:
            self.logger.error(f"Erreur lors du scan des anomalies: {str(e)}", exc_info=True)
            return Response({
                'error': f"Erreur lors du scan des anomalies: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)