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
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._anomalies_detected = False

    def _is_timesheet_matching_schedule(self, timesheet, schedule):
        """Vérifie si un pointage correspond à un planning"""
        # Vérifier si le planning est valide
        if not schedule or not schedule.is_active:
            self.logger.debug(f"Planning {schedule.id if schedule else 'None'} non valide ou inactif")
            return False

        # Récupérer les informations nécessaires
        timestamp = timesheet.timestamp
        local_timestamp = timezone.localtime(timestamp)
        current_date = local_timestamp.date()
        current_weekday = current_date.weekday()  # 0 = Lundi, 6 = Dimanche
        current_time = local_timestamp.time()
        entry_type = timesheet.entry_type

        self.logger.debug(f"Vérification de correspondance: {timesheet.employee.get_full_name()} - {schedule.site.name} - "
                         f"{local_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({current_time}) - {entry_type}")

        # Vérifier si le planning a des détails pour ce jour
        try:
            schedule_detail = ScheduleDetail.objects.get(
                schedule=schedule,
                day_of_week=current_weekday
            )

            # Pour les plannings fixes, vérifier les horaires
            if schedule.schedule_type == 'FIXED':
                day_type = schedule_detail.day_type
                self.logger.debug(f"Planning fixe - Type de journée: {schedule_detail.get_day_type_display()}")

                # Vérifier les horaires du matin
                if day_type in ['FULL', 'AM'] and schedule_detail.start_time_1 and schedule_detail.end_time_1:
                    self.logger.debug(f"Horaires matin: {schedule_detail.start_time_1}-{schedule_detail.end_time_1}")
                    # Si l'heure est dans la plage du matin ou proche
                    if (schedule_detail.start_time_1 <= current_time <= schedule_detail.end_time_1):
                        self.logger.debug(f"Correspondance avec les horaires du matin")
                        return True

                # Vérifier les horaires de l'après-midi
                if day_type in ['FULL', 'PM'] and schedule_detail.start_time_2 and schedule_detail.end_time_2:
                    self.logger.debug(f"Horaires après-midi: {schedule_detail.start_time_2}-{schedule_detail.end_time_2}")
                    # Si l'heure est dans la plage de l'après-midi ou proche
                    if (schedule_detail.start_time_2 <= current_time <= schedule_detail.end_time_2):
                        self.logger.debug(f"Correspondance avec les horaires de l'après-midi")
                        return True

                self.logger.debug(f"Pas de correspondance avec les horaires du planning fixe")

            # Pour les plannings fréquence, tout pointage est valide
            elif schedule.schedule_type == 'FREQUENCY':
                self.logger.debug(f"Planning fréquence - Durée attendue: {schedule_detail.frequency_duration} minutes")
                return True

        except ScheduleDetail.DoesNotExist:
            # Pas de planning pour ce jour
            self.logger.debug(f"Pas de détails de planning pour le jour {current_weekday}")
            return False

        return False

    def _find_employee_schedule(self, employee, site, date):
        """Trouve le planning associé à un employé et un site pour une date donnée."""
        self.logger.debug(f"Recherche du planning pour {employee.get_full_name()} (ID: {employee.id}) au site {site.name} (ID: {site.id}) le {date}")

        # Récupérer les relations site-employé pour cet employé et ce site
        site_employee_relations = SiteEmployee.objects.filter(
            site=site,
            employee=employee,
            is_active=True
        ).select_related('schedule')

        self.logger.debug(f"  {site_employee_relations.count()} relations site-employé trouvées")

        # Parcourir les relations pour trouver un planning actif pour cette date
        for site_employee in site_employee_relations:
            schedule = site_employee.schedule
            if not schedule or not schedule.is_active:
                self.logger.debug(f"  Relation {site_employee.id}: Pas de planning actif")
                continue

            # Afficher les informations détaillées du planning
            self.logger.debug(f"  Relation {site_employee.id}: Planning {schedule.id} - Type: {schedule.schedule_type}")

            # Afficher les marges de tolérance selon le type de planning
            if schedule.schedule_type == 'FIXED':
                self.logger.debug(f"    Marges de tolérance: Retard={schedule.late_arrival_margin or site.late_margin} min, "
                                 f"Départ anticipé={schedule.early_departure_margin or site.early_departure_margin} min")
            elif schedule.schedule_type == 'FREQUENCY':
                self.logger.debug(f"    Tolérance fréquence: {schedule.frequency_tolerance_percentage or site.frequency_tolerance}%")

            # Vérifier si le planning a des détails pour ce jour
            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=date.weekday()
                )

                # Afficher les détails du planning selon son type
                if schedule.schedule_type == 'FIXED':
                    day_type = schedule_detail.day_type
                    self.logger.debug(f"    Détails du planning pour {schedule_detail.get_day_of_week_display()} (jour {date.weekday()})")
                    self.logger.debug(f"    Type de journée: {schedule_detail.get_day_type_display()}")

                    if day_type in ['FULL', 'AM'] and schedule_detail.start_time_1 and schedule_detail.end_time_1:
                        self.logger.debug(f"    Matin: {schedule_detail.start_time_1}-{schedule_detail.end_time_1}")

                    if day_type in ['FULL', 'PM'] and schedule_detail.start_time_2 and schedule_detail.end_time_2:
                        self.logger.debug(f"    Après-midi: {schedule_detail.start_time_2}-{schedule_detail.end_time_2}")
                elif schedule.schedule_type == 'FREQUENCY':
                    self.logger.debug(f"    Détails du planning fréquence pour {schedule_detail.get_day_of_week_display()} (jour {date.weekday()})")
                    self.logger.debug(f"    Durée attendue: {schedule_detail.frequency_duration} minutes")

                # Planning trouvé pour ce jour
                return schedule
            except ScheduleDetail.DoesNotExist:
                self.logger.debug(f"  Pas de détails de planning pour le jour {date.weekday()}")
                # Pas de planning pour ce jour
                continue

        # Aucun planning trouvé
        self.logger.debug(f"  Aucun planning correspondant trouvé")
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

        created_anomalies = []

        site_employee_relations = SiteEmployee.objects.filter(
            site=site,
            employee=employee,
            is_active=True
        ).select_related('schedule')

        is_ambiguous = False
        is_out_of_schedule = True
        # Variable pour stocker le planning correspondant
        schedule_for_anomaly = None

        if not site_employee_relations.exists():
            timesheet.is_out_of_schedule = True
            timesheet.save()

            anomaly = Anomaly.objects.create(
                employee=employee,
                site=site,
                timesheet=timesheet,
                date=current_date,
                anomaly_type=Anomaly.AnomalyType.OTHER,
                description=f"Pointage hors planning: l'employé n'est pas rattaché à ce site.",
                status=Anomaly.AnomalyStatus.PENDING
            )
            self._anomalies_detected = True
            created_anomalies.append(anomaly)
            self.logger.info(f"Anomalie créée: OTHER - L'employé {employee.get_full_name()} n'est pas rattaché au site {site.name}")
            return True, created_anomalies

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
                                        anomaly = self._create_late_anomaly(timesheet, late_minutes, late_margin, schedule)
                                        if anomaly:
                                            created_anomalies.append(anomaly)

                        if schedule_detail.start_time_2 and schedule_detail.end_time_2 and not is_matching:
                            if schedule_detail.start_time_2 <= current_time <= schedule_detail.end_time_2:
                                is_matching = True
                                if current_time > schedule_detail.start_time_2:
                                    late_minutes = int((datetime.combine(current_date, current_time) -
                                                    datetime.combine(current_date, schedule_detail.start_time_2)).total_seconds() / 60)

                                    if late_minutes > late_margin:
                                        timesheet.is_late = True
                                        timesheet.late_minutes = late_minutes
                                        anomaly = self._create_late_anomaly(timesheet, late_minutes, late_margin, schedule)
                                        if anomaly:
                                            created_anomalies.append(anomaly)

                    elif entry_type == Timesheet.EntryType.DEPARTURE:
                        if schedule_detail.end_time_1 and current_time < schedule_detail.end_time_1:
                            is_matching = True
                            early_minutes = int((datetime.combine(current_date, schedule_detail.end_time_1) -
                                            datetime.combine(current_date, current_time)).total_seconds() / 60)

                            if early_minutes > early_departure_margin:
                                timesheet.is_early_departure = True
                                timesheet.early_departure_minutes = early_minutes
                                anomaly = self._create_early_departure_anomaly(timesheet, early_minutes, early_departure_margin, schedule)
                                if anomaly:
                                    created_anomalies.append(anomaly)

                        elif schedule_detail.end_time_2 and current_time < schedule_detail.end_time_2:
                            is_matching = True
                            early_minutes = int((datetime.combine(current_date, schedule_detail.end_time_2) -
                                            datetime.combine(current_date, current_time)).total_seconds() / 60)

                            if early_minutes > early_departure_margin:
                                timesheet.is_early_departure = True
                                timesheet.early_departure_minutes = early_minutes
                                anomaly = self._create_early_departure_anomaly(timesheet, early_minutes, early_departure_margin, schedule)
                                if anomaly:
                                    created_anomalies.append(anomaly)

                    if is_matching:
                        matching_schedules.append(schedule)
                        is_out_of_schedule = False
                        schedule_for_anomaly = schedule

                elif schedule.schedule_type == Schedule.ScheduleType.FREQUENCY:
                    matching_schedules.append(schedule)
                    is_out_of_schedule = False
                    schedule_for_anomaly = schedule

                    if entry_type == Timesheet.EntryType.DEPARTURE:
                        expected_duration = schedule_detail.frequency_duration
                        if expected_duration and expected_duration > 0:
                            # Récupérer la tolérance de fréquence (pourcentage)
                            tolerance_percentage = schedule.frequency_tolerance_percentage or site.frequency_tolerance or 10
                            self.logger.info(f"Tolérance de fréquence: {tolerance_percentage}% pour {schedule} (ID: {schedule.id})")

                            # Calculer la durée minimale requise avec la tolérance
                            min_duration = expected_duration * (1 - tolerance_percentage / 100)
                            self.logger.info(f"Durée attendue: {expected_duration} minutes, durée minimale avec tolérance: {min_duration:.1f} minutes")

                            # Trouver le dernier pointage d'arrivée pour cet employé et ce site
                            last_arrival = Timesheet.objects.filter(
                                employee=employee,
                                site=site,
                                entry_type=Timesheet.EntryType.ARRIVAL,
                                timestamp__date=current_date,
                                timestamp__lt=timestamp
                            ).order_by('-timestamp').first()

                            if last_arrival:
                                # Calculer la durée effective entre l'arrivée et le départ
                                duration_minutes = (timestamp - last_arrival.timestamp).total_seconds() / 60
                                self.logger.info(f"Durée effective: {duration_minutes:.1f} minutes entre {last_arrival.timestamp} et {timestamp}")

                                # Vérifier si la durée est inférieure à la durée minimale requise
                                if duration_minutes < min_duration:
                                    timesheet.is_early_departure = True
                                    early_minutes = int(min_duration - duration_minutes)
                                    timesheet.early_departure_minutes = early_minutes
                                    self.logger.info(f"Départ anticipé détecté: {early_minutes} minutes manquantes")

                                    # Vérifier si une anomalie similaire existe déjà
                                    existing_anomaly = Anomaly.objects.filter(
                                        employee=employee,
                                        site=site,
                                        date=current_date,
                                        anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                                        minutes=early_minutes
                                    ).first()

                                    if not existing_anomaly:
                                        # Créer une anomalie pour le départ anticipé en mode fréquence
                                        anomaly = Anomaly.objects.create(
                                            employee=employee,
                                            site=site,
                                            timesheet=timesheet,
                                            date=current_date,
                                            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                                            description=f'Durée insuffisante: {duration_minutes:.1f} minutes au lieu de {min_duration:.1f} minutes minimum (tolérance: {tolerance_percentage}%).',
                                            minutes=early_minutes,
                                            status=Anomaly.AnomalyStatus.PENDING,
                                            schedule=schedule
                                        )
                                        anomaly.related_timesheets.add(timesheet)
                                        self._anomalies_detected = True
                                        created_anomalies.append(anomaly)
                                        self.logger.info(f"Anomalie créée: EARLY_DEPARTURE (fréquence) - Durée insuffisante: {duration_minutes:.1f}min au lieu de {min_duration:.1f}min pour {employee.get_full_name()} à {site.name}")
                                    else:
                                        self.logger.info(f"Anomalie existante trouvée pour la durée insuffisante de {employee.get_full_name()} à {site.name}, pas de création de doublon")
                                else:
                                    self.logger.info(f"Durée suffisante: {duration_minutes:.1f} minutes >= {min_duration:.1f} minutes minimales requises")

            except ScheduleDetail.DoesNotExist:
                continue

        if len(matching_schedules) > 1:
            is_ambiguous = True
            most_recent_schedule = max(matching_schedules, key=lambda s: s.created_at)
            schedule_for_anomaly = most_recent_schedule

        timesheet.is_out_of_schedule = is_out_of_schedule
        timesheet.is_ambiguous = is_ambiguous
        timesheet.save()

        if is_out_of_schedule:
            anomaly = self._create_out_of_schedule_anomaly(timesheet)
            if anomaly:
                created_anomalies.append(anomaly)

        return is_ambiguous, created_anomalies

    def _create_late_anomaly(self, timesheet, late_minutes, late_margin, schedule):
        """Crée une anomalie de retard"""
        # Vérifier si une anomalie similaire existe déjà pour ce pointage ou cette date/employé/site
        existing_anomaly = Anomaly.objects.filter(
            employee=timesheet.employee,
            site=timesheet.site,
            date=timesheet.timestamp.date(),
            anomaly_type=Anomaly.AnomalyType.LATE,
            minutes=late_minutes
        ).first()

        created_anomaly = None
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
            created_anomaly = anomaly
            self.logger.info(f"Anomalie créée: LATE - Retard de {late_minutes} minutes (marge: {late_margin}min) pour {timesheet.employee.get_full_name()} à {timesheet.site.name}")

        return created_anomaly

    def _create_early_departure_anomaly(self, timesheet, early_minutes, early_departure_margin, schedule):
        """Crée une anomalie de départ anticipé"""
        # Vérifier si une anomalie similaire existe déjà pour ce pointage ou cette date/employé/site
        existing_anomaly = Anomaly.objects.filter(
            employee=timesheet.employee,
            site=timesheet.site,
            date=timesheet.timestamp.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
            minutes=early_minutes
        ).first()

        created_anomaly = None
        # Ne créer l'anomalie que si le départ est réellement anticipé (minutes > 0) et dépasse la marge
        if not existing_anomaly and early_minutes > 0 and early_minutes > early_departure_margin:
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
            created_anomaly = anomaly
            self.logger.info(f"Anomalie créée: EARLY_DEPARTURE - Départ anticipé de {early_minutes} minutes (marge: {early_departure_margin}min) pour {timesheet.employee.get_full_name()} à {timesheet.site.name}")
        elif early_minutes == 0:
            self.logger.debug(f"Départ exactement à l'heure de fin, pas d'anomalie créée pour {timesheet.employee.get_full_name()} à {timesheet.site.name}")
        elif early_minutes <= early_departure_margin:
            self.logger.debug(f"Départ anticipé de {early_minutes} minutes dans la marge de tolérance ({early_departure_margin}min) pour {timesheet.employee.get_full_name()} à {timesheet.site.name}")

        return created_anomaly

    def _create_out_of_schedule_anomaly(self, timesheet):
        """Crée une anomalie de pointage hors planning"""
        # Vérifier si une anomalie similaire existe déjà pour ce pointage ou cette date/employé/site
        existing_anomaly = Anomaly.objects.filter(
            employee=timesheet.employee,
            site=timesheet.site,
            date=timesheet.timestamp.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER,
            description__contains="Pointage hors planning"
        ).first()

        created_anomaly = None
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
            created_anomaly = anomaly
            self.logger.info(f"Anomalie créée: OTHER - Pointage hors planning pour {timesheet.employee.get_full_name()} à {timesheet.site.name}")

        return created_anomaly

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
            is_ambiguous, created_anomalies = self._match_schedule_and_check_anomalies(timesheet)

            return {
                'success': True,
                'message': 'Pointage traité avec succès',
                'is_ambiguous': is_ambiguous,
                'has_anomalies': self._anomalies_detected,
                'anomalies': created_anomalies
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

                self.logger.info(f"Début du scan des anomalies du {start_date} au {end_date}")
                if site_id:
                    site = Site.objects.get(id=site_id)
                    self.logger.info(f"Filtrage par site: {site.name} (ID: {site.id})")
                if employee_id:
                    employee = User.objects.get(id=employee_id)
                    self.logger.info(f"Filtrage par employé: {employee.get_full_name()} (ID: {employee.id})")

                # Construire la requête de base
                timesheets = Timesheet.objects.filter(
                    timestamp__date__gte=start_date,
                    timestamp__date__lte=end_date
                ).order_by('timestamp')  # Important: traiter les pointages dans l'ordre chronologique

                if site_id:
                    timesheets = timesheets.filter(site_id=site_id)
                if employee_id:
                    timesheets = timesheets.filter(employee_id=employee_id)

                self.logger.info(f"Nombre de pointages à traiter: {timesheets.count()}")

                # Si force_update est True, supprimer toutes les anomalies existantes
                if force_update:
                    self.logger.info("Mode force_update activé: suppression des anomalies existantes")
                    anomalies_filter = Q(date__gte=start_date, date__lte=end_date)
                    if site_id:
                        anomalies_filter &= Q(site_id=site_id)
                    if employee_id:
                        anomalies_filter &= Q(employee_id=employee_id)

                    anomalies_count = Anomaly.objects.filter(anomalies_filter).count()
                    Anomaly.objects.filter(anomalies_filter).delete()
                    self.logger.info(f"{anomalies_count} anomalies supprimées")

                    # Réinitialiser les statuts des pointages
                    self.logger.info("Réinitialisation des statuts des pointages")
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
                processed_count = 0
                for timesheet in timesheets:
                    processed_count += 1
                    if processed_count % 100 == 0:  # Log tous les 100 pointages pour éviter de surcharger les logs
                        self.logger.info(f"Progression: {processed_count}/{timesheets.count()} pointages traités")

                    result = self.process_timesheet(timesheet, force_update=force_update)
                    if result['success'] and result.get('has_anomalies', False):
                        anomalies_created += 1
                        if 'anomalies' in result and result['anomalies']:
                            for anomaly in result['anomalies']:
                                self.logger.debug(f"Anomalie détectée: {anomaly.anomaly_type} - {anomaly.description}")

                self.logger.info(f"Scan terminé: {anomalies_created} anomalies détectées sur {processed_count} pointages traités")
                return Response({
                    'message': f'{anomalies_created} anomalies traitées',
                    'anomalies_created': anomalies_created,
                    'timesheets_processed': processed_count,
                    'force_update': force_update,
                    'period': f"{start_date} au {end_date}"
                })

        except Exception as e:
            self.logger.error(f"Erreur lors du scan des anomalies: {str(e)}", exc_info=True)
            return Response({
                'error': f"Erreur lors du scan des anomalies: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)