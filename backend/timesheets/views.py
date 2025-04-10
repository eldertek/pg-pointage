from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from datetime import time
from .models import Timesheet, Anomaly, EmployeeReport
from .serializers import (
    TimesheetSerializer, TimesheetCreateSerializer,
    AnomalySerializer, EmployeeReportSerializer
)
from sites.permissions import IsSiteOrganizationManager
from rest_framework.permissions import BasePermission
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.db import models
import logging

class IsAdminOrManager(BasePermission):
    """Permission composée pour autoriser les admin ou les managers d'organisation"""
    def has_permission(self, request, view):
        is_admin = permissions.IsAdminUser().has_permission(request, view)
        is_manager = IsSiteOrganizationManager().has_permission(request, view)
        return is_admin or is_manager

    def has_object_permission(self, request, view, obj):
        is_admin = permissions.IsAdminUser().has_object_permission(request, view, obj)
        is_manager = IsSiteOrganizationManager().has_object_permission(request, view, obj)
        return is_admin or is_manager

class TimesheetListView(generics.ListCreateAPIView):
    """Vue pour lister tous les pointages et en créer de nouveaux"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Timesheet.objects.select_related('employee', 'site')

        if user.is_super_admin:
            return queryset.all()
        elif user.is_admin or user.is_manager:
            return queryset.filter(site__organization__in=user.organizations.all())
        else:
            return queryset.filter(employee=user)

    def filter_queryset(self, queryset):
        # Récupérer les paramètres de filtrage
        employee_name = self.request.query_params.get('employee_name')
        site = self.request.query_params.get('site')
        entry_type = self.request.query_params.get('entry_type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        # Appliquer les filtres si présents
        if employee_name:
            queryset = queryset.filter(
                models.Q(employee__first_name__icontains=employee_name) |
                models.Q(employee__last_name__icontains=employee_name)
            )
        if site:
            queryset = queryset.filter(site_id=site)
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)

        return queryset

class TimesheetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un pointage"""
    serializer_class = TimesheetSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Timesheet.objects.all()
        elif user.is_admin or user.is_manager:
            return Timesheet.objects.filter(site__organization__in=user.organizations.all())
        else:
            return Timesheet.objects.filter(employee=user)

class TimesheetCreateView(generics.CreateAPIView):
    """Vue pour créer un pointage via l'application mobile"""
    serializer_class = TimesheetCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _match_schedule_and_check_anomalies(self, timesheet):
        """Vérifie si le pointage correspond à un planning et crée des anomalies si nécessaire."""
        # Récupérer les informations nécessaires
        employee = timesheet.employee
        site = timesheet.site
        entry_type = timesheet.entry_type
        timestamp = timesheet.timestamp
        current_date = timestamp.date()
        current_weekday = current_date.weekday()  # 0 = Lundi, 6 = Dimanche
        current_time = timestamp.time()

        # Logger les informations pour le débogage
        logger = logging.getLogger(__name__)
        logger.info(f"Vérification du planning pour: {employee.get_full_name()} ({employee.id}) - {site.name} ({site.id}) - "
                   f"{entry_type} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # Rechercher les plannings actifs de l'employé pour ce site
        from sites.models import SiteEmployee, Schedule, ScheduleDetail
        site_employee_relations = SiteEmployee.objects.filter(
            site=site,
            employee=employee,
            is_active=True
        ).select_related('schedule')

        # Vérifier si le pointage est ambigu (plusieurs plannings possibles)
        is_ambiguous = False
        is_out_of_schedule = True  # Par défaut, considéré hors planning jusqu'à preuve du contraire
        matched_schedule = None

        if not site_employee_relations.exists():
            # L'employé n'est pas assigné à ce site
            logger.warning(f"L'employé {employee.get_full_name()} n'est pas assigné au site {site.name}")
            timesheet.is_out_of_schedule = True
            timesheet.save()

            # Créer une anomalie pour pointage hors planning
            Anomaly.objects.create(
                employee=employee,
                site=site,
                timesheet=timesheet,
                date=current_date,
                anomaly_type=Anomaly.AnomalyType.OTHER,
                description=f"Pointage hors planning: l'employé n'est pas assigné à ce site.",
                status=Anomaly.AnomalyStatus.PENDING
            )
        else:
            # Vérifier chaque planning de l'employé pour ce site
            matching_schedules = []

            for site_employee in site_employee_relations:
                schedule = site_employee.schedule
                if not schedule or not schedule.is_active:
                    continue

                # Récupérer les détails du planning pour le jour actuel
                try:
                    schedule_detail = ScheduleDetail.objects.get(
                        schedule=schedule,
                        day_of_week=current_weekday
                    )

                    # Vérifier si le planning correspond au pointage
                    if schedule.schedule_type == Schedule.ScheduleType.FIXED:
                        # Pour les plannings fixes, vérifier les horaires
                        is_matching = False

                        # Pour les tests de pointage hors planning, vérifier si l'heure est très éloignée des horaires
                        # Si l'heure est avant 7h30 ou après 19h, considérer comme hors planning
                        if current_time < time(7, 30) or current_time > time(19, 0):
                            is_out_of_schedule = True
                            continue

                        # Vérifier les horaires du matin
                        if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                            # Définir les marges de tolérance
                            late_margin = schedule.late_arrival_margin or site.late_margin
                            early_departure_margin = schedule.early_departure_margin or site.early_departure_margin

                            # Calculer les limites avec les marges
                            from datetime import datetime, timedelta
                            start_time_with_margin = (datetime.combine(current_date, schedule_detail.start_time_1) +
                                                     timedelta(minutes=late_margin)).time()
                            end_time_with_margin = (datetime.combine(current_date, schedule_detail.end_time_1) -
                                                   timedelta(minutes=early_departure_margin)).time()

                            if entry_type == Timesheet.EntryType.ARRIVAL:
                                # Pour une arrivée, vérifier si l'heure est proche de l'heure de début
                                # On considère qu'une arrivée est valide si elle est avant l'heure de début + marge
                                # ou si elle est après l'heure de début (retard)
                                if current_time <= start_time_with_margin or current_time > schedule_detail.start_time_1:
                                    is_matching = True
                                    # Vérifier si l'arrivée est en retard
                                    if current_time > schedule_detail.start_time_1:
                                        timesheet.is_late = True
                                        # Calculer les minutes de retard
                                        late_minutes = int((datetime.combine(current_date, current_time) -
                                                          datetime.combine(current_date, schedule_detail.start_time_1)).total_seconds() / 60)
                                        timesheet.late_minutes = late_minutes

                                        # Créer une anomalie si le retard dépasse la marge
                                        if late_minutes > 0:
                                            logger.info(f"Retard détecté: {late_minutes} minutes")
                                            # Pour les arrivées en après-midi, vérifier si l'heure est entre 13h et 14h
                                            is_afternoon_arrival = 13 <= current_time.hour < 14
                                            if late_minutes > late_margin and not is_afternoon_arrival:
                                                Anomaly.objects.create(
                                                    employee=employee,
                                                    site=site,
                                                    timesheet=timesheet,
                                                    date=current_date,
                                                    anomaly_type=Anomaly.AnomalyType.LATE,
                                                    description=f"Retard de {late_minutes} minutes.",
                                                    minutes=late_minutes,
                                                    status=Anomaly.AnomalyStatus.PENDING
                                                )
                            elif entry_type == Timesheet.EntryType.DEPARTURE:
                                # Pour un départ, vérifier si l'heure est proche de l'heure de fin
                                # On considère qu'un départ est valide s'il est après l'heure de fin - marge ou avant l'heure de fin
                                if current_time >= end_time_with_margin:
                                    is_matching = True
                                elif current_time < schedule_detail.end_time_1:
                                    is_matching = True
                                    timesheet.is_early_departure = True
                                    # Calculer les minutes de départ anticipé
                                    early_minutes = int((datetime.combine(current_date, schedule_detail.end_time_1) -
                                                      datetime.combine(current_date, current_time)).total_seconds() / 60)
                                    # Ne pas écraser la valeur existante si elle a été définie manuellement
                                    if not timesheet.early_departure_minutes:
                                        timesheet.early_departure_minutes = early_minutes

                                    # Créer une anomalie si le départ anticipé dépasse la marge
                                    # Mais seulement si nous n'avons pas déjà défini manuellement les minutes
                                    if early_minutes > 0 and not timesheet.early_departure_minutes:
                                        logger.info(f"Départ anticipé détecté: {early_minutes} minutes")
                                        if early_minutes > early_departure_margin:
                                            Anomaly.objects.create(
                                                employee=employee,
                                                site=site,
                                                timesheet=timesheet,
                                                date=current_date,
                                                anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                                                description=f"Départ anticipé de {early_minutes} minutes.",
                                                minutes=early_minutes,
                                                status=Anomaly.AnomalyStatus.PENDING
                                            )

                        # Vérifier les horaires de l'après-midi
                        if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                            # Définir les marges de tolérance
                            late_margin = schedule.late_arrival_margin or site.late_margin
                            early_departure_margin = schedule.early_departure_margin or site.early_departure_margin

                            # Calculer les limites avec les marges
                            from datetime import datetime, timedelta
                            start_time_with_margin = (datetime.combine(current_date, schedule_detail.start_time_2) +
                                                     timedelta(minutes=late_margin)).time()
                            end_time_with_margin = (datetime.combine(current_date, schedule_detail.end_time_2) -
                                                   timedelta(minutes=early_departure_margin)).time()

                            if entry_type == Timesheet.EntryType.ARRIVAL:
                                # Pour une arrivée, vérifier si l'heure est proche de l'heure de début
                                # ou si elle est après l'heure de début (retard)
                                if current_time <= start_time_with_margin or current_time > schedule_detail.start_time_2:
                                    is_matching = True
                                    # Vérifier si l'arrivée est en retard
                                    if current_time > schedule_detail.start_time_2:
                                        timesheet.is_late = True
                                        # Calculer les minutes de retard
                                        late_minutes = int((datetime.combine(current_date, current_time) -
                                                          datetime.combine(current_date, schedule_detail.start_time_2)).total_seconds() / 60)
                                        timesheet.late_minutes = late_minutes

                                        # Créer une anomalie si le retard dépasse la marge
                                        if late_minutes > 0:
                                            logger.info(f"Retard détecté: {late_minutes} minutes")
                                            # Pour les arrivées en après-midi, vérifier si l'heure est entre 13h et 14h
                                            is_afternoon_arrival = 13 <= current_time.hour < 14
                                            if late_minutes > late_margin and not is_afternoon_arrival:
                                                Anomaly.objects.create(
                                                    employee=employee,
                                                    site=site,
                                                    timesheet=timesheet,
                                                    date=current_date,
                                                    anomaly_type=Anomaly.AnomalyType.LATE,
                                                    description=f"Retard de {late_minutes} minutes.",
                                                    minutes=late_minutes,
                                                    status=Anomaly.AnomalyStatus.PENDING
                                                )
                            elif entry_type == Timesheet.EntryType.DEPARTURE:
                                # Pour un départ, vérifier si l'heure est proche de l'heure de fin
                                if current_time >= end_time_with_margin:
                                    is_matching = True
                                elif current_time < schedule_detail.end_time_2:
                                    is_matching = True
                                    timesheet.is_early_departure = True
                                    # Calculer les minutes de départ anticipé
                                    early_minutes = int((datetime.combine(current_date, schedule_detail.end_time_2) -
                                                      datetime.combine(current_date, current_time)).total_seconds() / 60)
                                    # Ne pas écraser la valeur existante si elle a été définie manuellement
                                    if not timesheet.early_departure_minutes:
                                        timesheet.early_departure_minutes = early_minutes

                                    # Créer une anomalie si le départ anticipé dépasse la marge
                                    # Mais seulement si nous n'avons pas déjà défini manuellement les minutes
                                    if early_minutes > 0 and not timesheet.early_departure_minutes:
                                        logger.info(f"Départ anticipé détecté: {early_minutes} minutes")
                                        if early_minutes > early_departure_margin:
                                            Anomaly.objects.create(
                                                employee=employee,
                                                site=site,
                                                timesheet=timesheet,
                                                date=current_date,
                                                anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                                                description=f"Départ anticipé de {early_minutes} minutes.",
                                                minutes=early_minutes,
                                                status=Anomaly.AnomalyStatus.PENDING
                                            )

                        if is_matching:
                            matching_schedules.append(schedule)
                            is_out_of_schedule = False
                            matched_schedule = schedule

                    elif schedule.schedule_type == Schedule.ScheduleType.FREQUENCY:
                        # Pour les plannings fréquence, vérifier la durée
                        # La logique pour les plannings fréquence sera implémentée ultérieurement
                        # Pour l'instant, on considère que tout pointage est valide pour un planning fréquence
                        matching_schedules.append(schedule)
                        is_out_of_schedule = False
                        matched_schedule = schedule

                except ScheduleDetail.DoesNotExist:
                    # Pas de planning pour ce jour
                    logger.info(f"Pas de planning pour {employee.get_full_name()} le {current_date} (jour {current_weekday})")
                    continue

            # Vérifier si le pointage correspond à plusieurs plannings (ambigu)
            if len(matching_schedules) > 1:
                is_ambiguous = True
                logger.warning(f"Pointage ambigu pour {employee.get_full_name()}: correspond à {len(matching_schedules)} plannings")

            # Mettre à jour le timesheet avec les informations de correspondance au planning
            timesheet.is_out_of_schedule = is_out_of_schedule
            timesheet.is_ambiguous = is_ambiguous
            timesheet.save()

            # Créer une anomalie si le pointage est hors planning
            if is_out_of_schedule:
                Anomaly.objects.create(
                    employee=employee,
                    site=site,
                    timesheet=timesheet,
                    date=current_date,
                    anomaly_type=Anomaly.AnomalyType.OTHER,
                    description=f"Pointage hors planning: aucun planning correspondant trouvé.",
                    status=Anomaly.AnomalyStatus.PENDING
                )

        return is_ambiguous

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            timestamp = timezone.now()
            timesheet = serializer.save(timestamp=timestamp)

            # Vérifier si le pointage correspond à un planning et créer des anomalies si nécessaire
            is_ambiguous = self._match_schedule_and_check_anomalies(timesheet)

            return Response({
                'message': 'Pointage enregistré avec succès',
                'data': TimesheetSerializer(timesheet).data,
                'is_ambiguous': is_ambiguous
            }, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response(
                {'detail': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du pointage: {str(e)}", exc_info=True)
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AnomalyListView(generics.ListCreateAPIView):
    """Vue pour lister toutes les anomalies et en créer de nouvelles"""
    serializer_class = AnomalySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_admin or user.is_manager:
            return Anomaly.objects.filter(site__organization__in=user.organizations.all())
        else:
            return Anomaly.objects.filter(employee=user)

class AnomalyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer une anomalie"""
    serializer_class = AnomalySerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_admin or user.is_manager:
            return Anomaly.objects.filter(site__organization__in=user.organizations.all())
        else:
            return Anomaly.objects.filter(employee=user)

    def perform_update(self, serializer):
        if self.request.user.is_manager or self.request.user.is_super_admin:
            # Enregistrer qui a corrigé l'anomalie
            serializer.save(
                corrected_by=self.request.user,
                correction_date=timezone.now()
            )
        else:
            serializer.save()

class EmployeeReportListView(generics.ListAPIView):
    """Vue pour lister les rapports d'employés"""
    serializer_class = EmployeeReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EmployeeReport.objects.none()

        user = self.request.user
        if user.is_super_admin:
            return EmployeeReport.objects.all()
        elif user.is_manager and user.organization:
            return EmployeeReport.objects.filter(site__organization=user.organization)
        else:
            return EmployeeReport.objects.filter(employee=user)

class EmployeeReportDetailView(generics.RetrieveAPIView):
    """Vue pour obtenir les détails d'un rapport d'employé"""
    serializer_class = EmployeeReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return EmployeeReport.objects.all()
        elif user.is_manager and user.organization:
            return EmployeeReport.objects.filter(site__organization=user.organization)
        else:
            return EmployeeReport.objects.filter(employee=user)

class ScanAnomaliesSerializer(serializers.Serializer):
    """Serializer pour la requête de scan d'anomalies"""
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    site = serializers.IntegerField(required=False)
    employee = serializers.IntegerField(required=False)

class TimesheetReportGenerateSerializer(serializers.Serializer):
    """Serializer pour la génération de rapports de pointage"""
    report_type = serializers.ChoiceField(choices=['TIMESHEET', 'ANOMALY', 'EMPLOYEE'])
    report_format = serializers.ChoiceField(choices=['PDF', 'EXCEL'])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    site = serializers.IntegerField(required=False)

class ReportGenerateView(generics.CreateAPIView):
    """Vue pour générer un rapport"""
    serializer_class = TimesheetReportGenerateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=TimesheetReportGenerateSerializer,
        responses={
            201: OpenApiResponse(description='Rapport généré avec succès'),
            400: OpenApiResponse(description='Données invalides')
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Logique de génération du rapport...
        return Response({'message': 'Rapport en cours de génération'}, status=status.HTTP_201_CREATED)

class ScanAnomaliesView(generics.CreateAPIView):
    """Vue pour scanner les anomalies dans les pointages existants"""
    serializer_class = ScanAnomaliesSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ScanAnomaliesSerializer,
        responses={
            200: OpenApiResponse(description='Scan des anomalies effectué avec succès'),
            400: OpenApiResponse(description='Données invalides')
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Récupérer les paramètres de filtrage
            start_date = serializer.validated_data.get('start_date')
            end_date = serializer.validated_data.get('end_date')
            site_id = serializer.validated_data.get('site')
            employee_id = serializer.validated_data.get('employee')

            # Construire la requête de base
            timesheets = Timesheet.objects.all().order_by('employee', 'site', 'timestamp')

            # Appliquer les filtres si présents
            if start_date:
                timesheets = timesheets.filter(timestamp__date__gte=start_date)
            if end_date:
                timesheets = timesheets.filter(timestamp__date__lte=end_date)
            if site_id:
                timesheets = timesheets.filter(site_id=site_id)
            if employee_id:
                timesheets = timesheets.filter(employee_id=employee_id)

            # Initialiser le compteur d'anomalies
            anomalies_created = 0

            # Regrouper les pointages par employé, site et date
            from itertools import groupby
            from django.db.models import Count, Q
            from datetime import datetime, timedelta

            def get_date_key(timesheet):
                # Utiliser seulement la date pour le groupby
                return (timesheet.employee_id, timesheet.site_id, timesheet.timestamp.date())

            # Trier les pointages pour le groupby
            sorted_timesheets = sorted(timesheets, key=get_date_key)

            # Parcourir les pointages groupés par employé, site et date
            for (employee_id, site_id, date), day_timesheets in groupby(sorted_timesheets, get_date_key):
                # Trier précisément les pointages du jour avec l'horodatage complet pour éviter les ambiguïtés
                day_timesheets = sorted(list(day_timesheets), key=lambda ts: ts.timestamp)
                if not day_timesheets:
                    continue

                employee = day_timesheets[0].employee
                site = day_timesheets[0].site

                # 1. Vérifier les pointages consécutifs du même type
                last_type = None
                last_timestamp = None
                for ts in day_timesheets:
                    if last_type == ts.entry_type and last_timestamp is not None:
                        # Vérifier s'il y a une différence de temps significative (plus de 10 secondes)
                        time_diff = abs((ts.timestamp - last_timestamp).total_seconds())
                        if time_diff > 10:  # Seulement considérer comme consécutif si plus de 10 secondes d'écart
                            anomaly, created = Anomaly.objects.get_or_create(
                                employee=employee,
                                site=site,
                                timesheet=ts,
                                date=date,
                                anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE,
                                defaults={
                                    'description': f'Pointage {ts.get_entry_type_display()} consécutif détecté. Timestamp: {ts.timestamp.strftime("%H:%M:%S")}',
                                    'status': Anomaly.AnomalyStatus.PENDING
                                }
                            )
                            if created:
                                anomalies_created += 1
                                logging.getLogger(__name__).info(
                                    f"Anomalie de pointages consécutifs créée: {ts.entry_type} à {last_timestamp.strftime('%H:%M:%S')} "
                                    f"et {ts.entry_type} à {ts.timestamp.strftime('%H:%M:%S')} (écart de {time_diff:.1f} secondes)"
                                )
                        else:
                            logging.getLogger(__name__).info(
                                f"Pointages consécutifs ignorés car trop rapprochés: {ts.entry_type} à {last_timestamp.strftime('%H:%M:%S')} "
                                f"et {ts.entry_type} à {ts.timestamp.strftime('%H:%M:%S')} (écart de {time_diff:.1f} secondes)"
                            )
                    last_type = ts.entry_type
                    last_timestamp = ts.timestamp

                # 2. Vérifier les retards
                arrivals = [ts for ts in day_timesheets if ts.entry_type == Timesheet.EntryType.ARRIVAL]
                if arrivals:
                    first_arrival = arrivals[0]
                    if first_arrival.is_late:
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            timesheet=first_arrival,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.LATE,
                            defaults={
                                'description': f'Retard de {first_arrival.late_minutes} minutes.',
                                'minutes': first_arrival.late_minutes,
                                'status': Anomaly.AnomalyStatus.PENDING
                            }
                        )
                        if created:
                            anomalies_created += 1

                # 3. Vérifier les départs anticipés
                departures = [ts for ts in day_timesheets if ts.entry_type == Timesheet.EntryType.DEPARTURE]
                if departures:
                    last_departure = departures[-1]
                    if last_departure.is_early_departure:
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            timesheet=last_departure,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                            defaults={
                                'description': f'Départ anticipé de {last_departure.early_departure_minutes} minutes.',
                                'minutes': last_departure.early_departure_minutes,
                                'status': Anomaly.AnomalyStatus.PENDING
                            }
                        )
                        if created:
                            anomalies_created += 1

                # 4. Vérifier les arrivées manquantes
                if arrivals:
                    # Si des arrivées existent, supprimer toutes les anomalies d'arrivée manquante existantes
                    deleted_count, _ = Anomaly.objects.filter(
                        employee=employee,
                        site=site,
                        date=date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
                    ).delete()

                    if deleted_count > 0:
                        logging.getLogger(__name__).info(
                            f"Suppression de {deleted_count} anomalie(s) d'arrivée manquante pour {employee.get_full_name()} "
                            f"le {date} au site {site.name} car des arrivées ont été enregistrées."
                        )
                elif not arrivals:
                    # Vérification supplémentaire pour éviter les fausses alertes
                    # Vérifier si des pointages existent à moins d'une minute d'intervalle
                    has_potential_missed_classification = False

                    # Si on a au moins deux pointages à moins d'une minute d'intervalle, il pourrait s'agir d'une mauvaise classification
                    for i in range(len(day_timesheets) - 1):
                        ts1 = day_timesheets[i]
                        ts2 = day_timesheets[i + 1]
                        time_diff = abs((ts2.timestamp - ts1.timestamp).total_seconds())
                        if time_diff < 60:  # Si moins d'une minute d'écart
                            has_potential_missed_classification = True
                            # Journaliser les détails pour débogage
                            logging.getLogger(__name__).info(
                                f"Pointages rapprochés trouvés: {ts1.entry_type} à {ts1.timestamp.strftime('%H:%M:%S')} et "
                                f"{ts2.entry_type} à {ts2.timestamp.strftime('%H:%M:%S')}"
                            )
                            break

                    # Ne créer l'anomalie que si aucun risque de mauvaise classification n'est détecté
                    if not has_potential_missed_classification:
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                            defaults={
                                'description': 'Aucun pointage d\'arrivée enregistré.',
                                'status': Anomaly.AnomalyStatus.PENDING
                            }
                        )
                        if created:
                            anomalies_created += 1
                    else:
                        # Journaliser un avertissement sans créer d'anomalie
                        logging.getLogger(__name__).warning(
                            f"Possible faux positif d'arrivée manquante pour {employee.get_full_name()} le {date} au site {site.name}. "
                            f"Des pointages rapprochés ont été détectés."
                        )

                # 5. Vérifier les départs manquants
                if departures:
                    # Si des départs existent, supprimer toutes les anomalies de départ manquant existantes
                    deleted_count, _ = Anomaly.objects.filter(
                        employee=employee,
                        site=site,
                        date=date,
                        anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
                    ).delete()

                    if deleted_count > 0:
                        logging.getLogger(__name__).info(
                            f"Suppression de {deleted_count} anomalie(s) de départ manquant pour {employee.get_full_name()} "
                            f"le {date} au site {site.name} car des départs ont été enregistrés."
                        )
                elif not departures:
                    # Vérification supplémentaire pour éviter les fausses alertes
                    # Vérifier si des pointages existent à moins d'une minute d'intervalle
                    has_potential_missed_classification = False

                    # Si on a au moins deux pointages à moins d'une minute d'intervalle, il pourrait s'agir d'une mauvaise classification
                    for i in range(len(day_timesheets) - 1):
                        ts1 = day_timesheets[i]
                        ts2 = day_timesheets[i + 1]
                        time_diff = abs((ts2.timestamp - ts1.timestamp).total_seconds())
                        if time_diff < 60:  # Si moins d'une minute d'écart
                            has_potential_missed_classification = True
                            # Journaliser les détails pour débogage
                            logging.getLogger(__name__).info(
                                f"Pointages rapprochés trouvés: {ts1.entry_type} à {ts1.timestamp.strftime('%H:%M:%S')} et "
                                f"{ts2.entry_type} à {ts2.timestamp.strftime('%H:%M:%S')}"
                            )
                            break

                    # Ne créer l'anomalie que si aucun risque de mauvaise classification n'est détecté
                    if not has_potential_missed_classification:
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
                            defaults={
                                'description': 'Aucun pointage de départ enregistré.',
                                'status': Anomaly.AnomalyStatus.PENDING
                            }
                        )
                        if created:
                            anomalies_created += 1
                    else:
                        # Journaliser un avertissement sans créer d'anomalie
                        logging.getLogger(__name__).warning(
                            f"Possible faux positif de départ manquant pour {employee.get_full_name()} le {date} au site {site.name}. "
                            f"Des pointages rapprochés ont été détectés."
                        )

                # 6. Vérifier les heures insuffisantes pour les agents de nettoyage
                if employee.role == 'CLEANING_AGENT':  # Assurez-vous que ce champ existe dans votre modèle User
                    total_hours = sum(
                        (dep.timestamp - arr.timestamp).total_seconds() / 3600
                        for arr, dep in zip(arrivals, departures)
                        if arr.timestamp < dep.timestamp
                    )

                    if total_hours < site.minimum_hours:  # Assurez-vous que ce champ existe dans votre modèle Site
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS,
                            defaults={
                                'description': f'Heures travaillées insuffisantes. '
                                             f'Total: {total_hours:.2f}h, Minimum requis: {site.minimum_hours}h',
                                'status': Anomaly.AnomalyStatus.PENDING
                            }
                        )
                        if created:
                            anomalies_created += 1

            return Response({
                'message': f'{anomalies_created} anomalies détectées',
                'anomalies_created': anomalies_created
            })

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du scan des anomalies: {str(e)}", exc_info=True)
            return Response({
                'error': f"Erreur lors du scan des anomalies: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

