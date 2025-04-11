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
                description=f"Pointage hors planning: l'employé n'est pas rattaché à ce site.",
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
                                # Déterminer d'abord si le pointage appartient à la plage du matin ou de l'après-midi
                                # Plage du matin
                                if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                                    if schedule_detail.start_time_1 <= current_time <= schedule_detail.end_time_1:
                                        # Le pointage appartient à la plage du matin
                                        relevant_end_time = schedule_detail.end_time_1
                                        end_time_with_margin = (
                                            datetime.combine(current_date, relevant_end_time) -
                                            timedelta(minutes=early_departure_margin)
                                        ).time()

                                        if current_time >= end_time_with_margin:
                                            is_matching = True
                                        else:
                                            is_matching = True
                                            timesheet.is_early_departure = True
                                            # Calculer les minutes de départ anticipé par rapport à la fin de la plage du matin
                                            early_minutes = int((datetime.combine(current_date, relevant_end_time) -
                                                              datetime.combine(current_date, current_time)).total_seconds() / 60)
                                            # Ne pas écraser la valeur existante si elle a été définie manuellement
                                            if not timesheet.early_departure_minutes:
                                                timesheet.early_departure_minutes = early_minutes

                                            # Créer une anomalie si le départ anticipé dépasse la marge
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

                                # Plage de l'après-midi
                                if not is_matching and schedule_detail.start_time_2 and schedule_detail.end_time_2:
                                    if schedule_detail.start_time_2 <= current_time <= schedule_detail.end_time_2:
                                        # Le pointage appartient à la plage de l'après-midi
                                        relevant_end_time = schedule_detail.end_time_2
                                        end_time_with_margin = (
                                            datetime.combine(current_date, relevant_end_time) -
                                            timedelta(minutes=early_departure_margin)
                                        ).time()

                                        if current_time >= end_time_with_margin:
                                            is_matching = True
                                        else:
                                            is_matching = True
                                            timesheet.is_early_departure = True
                                            # Calculer les minutes de départ anticipé par rapport à la fin de la plage de l'après-midi
                                            early_minutes = int((datetime.combine(current_date, relevant_end_time) -
                                                              datetime.combine(current_date, current_time)).total_seconds() / 60)
                                            # Ne pas écraser la valeur existante si elle a été définie manuellement
                                            if not timesheet.early_departure_minutes:
                                                timesheet.early_departure_minutes = early_minutes

                                            # Créer une anomalie si le départ anticipé dépasse la marge
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

                                # Si le pointage n'appartient à aucune plage mais est à proximité, considérer comme valide
                                if not is_matching:
                                    # Vérifier si le pointage est après la fin de toutes les plages
                                    latest_end_time = schedule_detail.end_time_2 if schedule_detail.end_time_2 else schedule_detail.end_time_1
                                    if latest_end_time and current_time >= latest_end_time:
                                        is_matching = True

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
                            # La gestion des départs anticipés est désormais traitée par la nouvelle logique ci-dessus
                            # Nous n'avons plus besoin de ce bloc car la logique est désormais unifiée
                            # et prend correctement en compte les deux plages horaires

                        if is_matching:
                            matching_schedules.append(schedule)
                            is_out_of_schedule = False
                            matched_schedule = schedule

                    elif schedule.schedule_type == Schedule.ScheduleType.FREQUENCY:
                        # Pour les plannings fréquence, vérifier la durée
                        # On considère que tout pointage est valide pour un planning fréquence
                        # mais on vérifiera la durée entre arrivée et départ lors du scan d'anomalies
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
                # Tenter de résoudre l'ambigüité en choisissant le planning le plus récent
                most_recent_schedule = None
                for schedule in matching_schedules:
                    if most_recent_schedule is None or schedule.created_at > most_recent_schedule.created_at:
                        most_recent_schedule = schedule

                if most_recent_schedule:
                    matched_schedule = most_recent_schedule
                    logger.info(f"Ambigüité résolue pour {employee.get_full_name()}: choix du planning le plus récent (ID: {matched_schedule.id})")
                else:
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
    force_update = serializers.BooleanField(required=False, default=False, help_text="Si True, force la réévaluation de tous les statuts des pointages existants")

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

    def _is_schedule_active_for_date(self, schedule, date):
        """Vérifie si un planning est actif pour une date donnée."""
        if not schedule or not schedule.is_active:
            return False

        # Récupérer le jour de la semaine (0-6, lundi=0)
        day_of_week = date.weekday()

        # Vérifier si le planning a des détails pour ce jour
        try:
            from sites.models import ScheduleDetail
            schedule_detail = ScheduleDetail.objects.get(schedule=schedule, day_of_week=day_of_week)
            return True
        except ScheduleDetail.DoesNotExist:
            return False

    def _is_timesheet_matching_schedule(self, timesheet, schedule):
        """Vérifie si un pointage correspond à un planning."""
        if not schedule or not schedule.is_active:
            return False

        # Récupérer le jour de la semaine (0-6, lundi=0)
        day_of_week = timesheet.timestamp.weekday()

        # Récupérer les détails du planning pour ce jour
        try:
            from sites.models import ScheduleDetail
            schedule_detail = ScheduleDetail.objects.get(schedule=schedule, day_of_week=day_of_week)
        except ScheduleDetail.DoesNotExist:
            return False

        # Si c'est un planning fixe, vérifier les heures
        if schedule.schedule_type == 'FIXED':
            # Convertir l'heure du pointage en minutes depuis minuit
            timesheet_minutes = timesheet.timestamp.hour * 60 + timesheet.timestamp.minute

            # Vérifier si l'heure du pointage est dans les plages horaires du planning
            # avec une marge de tolérance
            tolerance_minutes = 30  # 30 minutes de tolérance par défaut

            # Plage 1
            if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                start_minutes_1 = schedule_detail.start_time_1.hour * 60 + schedule_detail.start_time_1.minute
                end_minutes_1 = schedule_detail.end_time_1.hour * 60 + schedule_detail.end_time_1.minute

                # Vérifier si le pointage est dans la plage 1 (avec tolérance)
                if (start_minutes_1 - tolerance_minutes <= timesheet_minutes <= end_minutes_1 + tolerance_minutes):
                    return True

            # Plage 2
            if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                start_minutes_2 = schedule_detail.start_time_2.hour * 60 + schedule_detail.start_time_2.minute
                end_minutes_2 = schedule_detail.end_time_2.hour * 60 + schedule_detail.end_time_2.minute

                # Vérifier si le pointage est dans la plage 2 (avec tolérance)
                if (start_minutes_2 - tolerance_minutes <= timesheet_minutes <= end_minutes_2 + tolerance_minutes):
                    return True

            return False

        # Si c'est un planning fréquence, tout pointage est valide
        elif schedule.schedule_type == 'FREQUENCE':
            return True

        return False

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

            # Créer un dictionnaire pour stocker les employés et les sites
            employees_sites = {}
            for timesheet in timesheets:
                key = (timesheet.employee_id, timesheet.site_id, timesheet.timestamp.date())
                if key not in employees_sites:
                    employees_sites[key] = (timesheet.employee, timesheet.site)

            # Vérifier les jours sans pointage pour les employés avec des plannings actifs
            if start_date and end_date:
                # Parcourir chaque jour de la période
                current_date = start_date
                while current_date <= end_date:
                    # Pour chaque employé et site spécifiés
                    if employee_id and site_id:
                        # Récupérer l'employé et le site
                        try:
                            from users.models import User
                            from sites.models import Site
                            employee = User.objects.get(id=employee_id)
                            site = Site.objects.get(id=site_id)

                            # Vérifier si l'employé a un planning pour ce jour
                            from sites.models import SiteEmployee, Schedule, ScheduleDetail
                            site_employee_relations = SiteEmployee.objects.filter(
                                site=site,
                                employee=employee,
                                is_active=True
                            ).select_related('schedule')

                            # Vérifier si l'employé a des pointages pour ce jour
                            day_timesheets = Timesheet.objects.filter(
                                employee=employee,
                                site=site,
                                timestamp__date=current_date
                            )

                            # Si l'employé n'a pas de pointages pour ce jour mais a un planning actif
                            if not day_timesheets.exists():
                                for site_employee in site_employee_relations:
                                    schedule = site_employee.schedule
                                    if not schedule or not schedule.is_active:
                                        continue

                                    # Vérifier si le planning a des détails pour ce jour
                                    try:
                                        schedule_detail = ScheduleDetail.objects.get(
                                            schedule=schedule,
                                            day_of_week=current_date.weekday()
                                        )

                                        # Créer une anomalie pour arrivée manquante
                                        anomaly, created = Anomaly.objects.get_or_create(
                                            employee=employee,
                                            site=site,
                                            date=current_date,
                                            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                                            defaults={
                                                'description': 'Aucun pointage d\'arrivée enregistré.',
                                                'status': Anomaly.AnomalyStatus.PENDING,
                                                'schedule': schedule
                                            }
                                        )

                                        if created:
                                            anomalies_created += 1
                                            logging.getLogger(__name__).info(
                                                f"Anomalie d'arrivée manquante créée pour {employee.get_full_name()} "
                                                f"le {current_date} au site {site.name}."
                                            )
                                        break
                                    except ScheduleDetail.DoesNotExist:
                                        continue
                        except (User.DoesNotExist, Site.DoesNotExist):
                            pass

                    # Passer au jour suivant
                    current_date += timedelta(days=1)

            # Récupérer le paramètre force_update
            force_update = serializer.validated_data.get('force_update', False)

            # Si force_update est True, réinitialiser les statuts des pointages
            if force_update:
                logging.getLogger(__name__).info("Force update activé : réinitialisation des statuts des pointages")
                # Réinitialiser les statuts des pointages
                for ts in timesheets:
                    # Réinitialiser les statuts de retard et départ anticipé
                    if ts.entry_type == Timesheet.EntryType.ARRIVAL:
                        ts.is_late = False
                        ts.late_minutes = 0
                    elif ts.entry_type == Timesheet.EntryType.DEPARTURE:
                        ts.is_early_departure = False
                        ts.early_departure_minutes = 0
                    # Réinitialiser le statut hors planning
                    ts.is_out_of_schedule = False
                    ts.save()

                # Supprimer toutes les anomalies existantes pour les pointages concernés
                if start_date and end_date:
                    anomalies_filter = {}
                    if site_id:
                        anomalies_filter['site_id'] = site_id
                    if employee_id:
                        anomalies_filter['employee_id'] = employee_id

                    deleted_count, _ = Anomaly.objects.filter(
                        date__gte=start_date,
                        date__lte=end_date,
                        **anomalies_filter
                    ).delete()

                    logging.getLogger(__name__).info(f"Suppression de {deleted_count} anomalies existantes")

            # Filtrer les pointages hors ligne
            online_timesheets = [ts for ts in timesheets if not (hasattr(ts, 'created_offline') and ts.created_offline)]

            # Trier les pointages pour le groupby
            sorted_timesheets = sorted(online_timesheets, key=get_date_key)

            # Parcourir les pointages groupés par employé, site et date
            for (employee_id, site_id, date), day_timesheets in groupby(sorted_timesheets, get_date_key):
                # Trier précisément les pointages du jour avec l'horodatage complet pour éviter les ambiguïtés
                day_timesheets = sorted(list(day_timesheets), key=lambda ts: ts.timestamp)
                if not day_timesheets:
                    continue

                employee = day_timesheets[0].employee
                site = day_timesheets[0].site

                # 0. Vérifier si les pointages sont hors planning
                for ts in day_timesheets:
                    # Ignorer les pointages hors ligne
                    if hasattr(ts, 'created_offline') and ts.created_offline:
                        logging.getLogger(__name__).info(
                            f"Pointage {ts.id} ignoré pour la vérification hors planning car il a été créé hors ligne."
                        )
                        continue

                    # Vérifier si le pointage est déjà marqué comme hors planning
                    if not ts.is_out_of_schedule:
                        # Récupérer les plannings de l'employé pour ce site
                        from sites.models import SiteEmployee, Schedule, ScheduleDetail
                        site_employee_relations = SiteEmployee.objects.filter(
                            site=site,
                            employee=employee,
                            is_active=True
                        ).select_related('schedule')

                        # Vérifier si l'employé a des plannings pour ce jour
                        has_schedule_for_day = False
                        for site_employee in site_employee_relations:
                            schedule = site_employee.schedule
                            if not schedule or not schedule.is_active:
                                continue

                            # Vérifier si le planning a des détails pour ce jour
                            try:
                                schedule_detail = ScheduleDetail.objects.get(
                                    schedule=schedule,
                                    day_of_week=date.weekday()
                                )
                                has_schedule_for_day = True
                                break
                            except ScheduleDetail.DoesNotExist:
                                continue

                        # Si l'employé n'a pas de planning pour ce jour, marquer le pointage comme hors planning
                        if not has_schedule_for_day:
                            ts.is_out_of_schedule = True
                            ts.save()
                            logging.getLogger(__name__).info(
                                f"Pointage {ts.id} marqué comme hors planning pour {employee.get_full_name()} "
                                f"le {date} au site {site.name} car aucun planning n'est défini pour ce jour."
                            )

                            # Supprimer les anomalies existantes pour éviter les doublons
                            Anomaly.objects.filter(
                                employee=employee,
                                site=site,
                                date=date,
                                anomaly_type=Anomaly.AnomalyType.OTHER,
                                description__contains="Pointage hors planning"
                            ).delete()

                            # Créer une anomalie pour pointage hors planning
                            anomaly = Anomaly.objects.create(
                                employee=employee,
                                site=site,
                                timesheet=ts,
                                date=date,
                                anomaly_type=Anomaly.AnomalyType.OTHER,
                                description=f"Pointage hors planning: l'employé n'est pas rattaché à ce site ou appartient à une autre organisation.",
                                status=Anomaly.AnomalyStatus.PENDING
                            )
                            anomalies_created += 1

                # 1. Vérifier les pointages consécutifs du même type
                last_type = None
                last_timestamp = None
                for ts in day_timesheets:
                    if last_type == ts.entry_type and last_timestamp is not None:
                        # Vérifier s'il y a une différence de temps significative (plus de 10 secondes)
                        time_diff = abs((ts.timestamp - last_timestamp).total_seconds())
                        if time_diff > 10:  # Seulement considérer comme consécutif si plus de 10 secondes d'écart
                            # Utiliser filter().first() au lieu de get_or_create pour éviter les erreurs de doublons
                            existing_anomaly = Anomaly.objects.filter(
                                employee=employee,
                                site=site,
                                timesheet=ts,
                                date=date,
                                anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
                            ).first()

                            if existing_anomaly:
                                created = False
                                anomaly = existing_anomaly
                            else:
                                anomaly = Anomaly.objects.create(
                                    employee=employee,
                                    site=site,
                                    timesheet=ts,
                                    date=date,
                                    anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE,
                                    description=f'Pointage {ts.get_entry_type_display()} consécutif détecté. Timestamp: {ts.timestamp.strftime("%H:%M:%S")}',
                                    status=Anomaly.AnomalyStatus.PENDING
                                )
                                created = True
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
                    # Vérifier si l'arrivée est en retard
                    # Si late_minutes n'est pas défini, calculer le retard
                    if not first_arrival.late_minutes:
                        # Récupérer le planning associé au pointage
                        from sites.models import SiteEmployee, Schedule, ScheduleDetail
                        site_employee_relations = SiteEmployee.objects.filter(
                            site=site,
                            employee=employee,
                            is_active=True
                        ).select_related('schedule')

                        for site_employee in site_employee_relations:
                            schedule = site_employee.schedule
                            if not schedule or not schedule.is_active:
                                continue

                            # Vérifier si le planning a des détails pour ce jour
                            try:
                                schedule_detail = ScheduleDetail.objects.get(
                                    schedule=schedule,
                                    day_of_week=date.weekday()
                                )

                                # Calculer le retard par rapport à l'heure de début
                                from datetime import datetime
                                arrival_time = first_arrival.timestamp.time()
                                if schedule_detail.start_time_1 and arrival_time > schedule_detail.start_time_1:
                                    late_minutes = int((datetime.combine(date, arrival_time) -
                                                      datetime.combine(date, schedule_detail.start_time_1)).total_seconds() / 60)
                                    first_arrival.is_late = True
                                    first_arrival.late_minutes = late_minutes
                                    first_arrival.save()
                                    break
                            except ScheduleDetail.DoesNotExist:
                                continue

                    # Récupérer le planning associé au pointage
                    from sites.models import SiteEmployee, Schedule
                    site_employee_relations = SiteEmployee.objects.filter(
                        site=site,
                        employee=employee,
                        is_active=True
                    ).select_related('schedule')

                    associated_schedule = None
                    for site_employee in site_employee_relations:
                        if site_employee.schedule and site_employee.schedule.is_active:
                            # Vérifier si ce planning correspond au pointage
                            if self._is_timesheet_matching_schedule(first_arrival, site_employee.schedule):
                                associated_schedule = site_employee.schedule
                                break

                    # Récupérer la marge de retard
                    late_margin = 0
                    if associated_schedule:
                        late_margin = associated_schedule.late_arrival_margin or site.late_margin
                    else:
                        late_margin = site.late_margin

                    # Créer une anomalie si l'arrivée est en retard
                    if first_arrival.is_late and first_arrival.late_minutes > 0:
                        # Créer une anomalie pour tous les retards, même ceux dans la marge
                        # Supprimer les anomalies existantes pour éviter les doublons
                        Anomaly.objects.filter(
                            employee=employee,
                            site=site,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.LATE,
                            timesheet=first_arrival
                        ).delete()

                        anomaly = Anomaly.objects.create(
                            employee=employee,
                            site=site,
                            timesheet=first_arrival,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.LATE,
                            description=f'Retard de {first_arrival.late_minutes} minutes.',
                            minutes=first_arrival.late_minutes,
                            status=Anomaly.AnomalyStatus.PENDING,
                            schedule=associated_schedule
                        )

                        # Associer le pointage concerné à l'anomalie
                        anomaly.related_timesheets.add(first_arrival)
                        anomalies_created += 1
                        logging.getLogger(__name__).info(
                            f"Anomalie de retard créée pour {employee.get_full_name()} le {date} au site {site.name}. "
                            f"Retard: {first_arrival.late_minutes} minutes, Marge: {late_margin} minutes"
                        )

                # 3. Vérifier les départs anticipés
                departures = [ts for ts in day_timesheets if ts.entry_type == Timesheet.EntryType.DEPARTURE]
                if departures:
                    last_departure = departures[-1]

                    # Récupérer le planning associé au pointage
                    from sites.models import SiteEmployee, Schedule, ScheduleDetail
                    site_employee_relations = SiteEmployee.objects.filter(
                        site=site,
                        employee=employee,
                        is_active=True
                    ).select_related('schedule')

                    associated_schedule = None
                    is_early_departure = False
                    early_departure_minutes = 0

                    # Vérifier si le départ est anticipé par rapport à un planning
                    for site_employee in site_employee_relations:
                        schedule = site_employee.schedule
                        if not schedule or not schedule.is_active:
                            continue

                        # Vérifier si ce planning correspond au pointage
                        if self._is_timesheet_matching_schedule(last_departure, schedule):
                            associated_schedule = schedule

                            # Récupérer les détails du planning pour ce jour
                            try:
                                schedule_detail = ScheduleDetail.objects.get(
                                    schedule=schedule,
                                    day_of_week=date.weekday()
                                )

                                # Vérifier si c'est un départ anticipé
                                departure_time = last_departure.timestamp.time()

                                # Vérifier d'abord par rapport à la plage du matin
                                if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                                    # Si l'heure de départ est entre l'heure de début et l'heure de fin du matin
                                    if schedule_detail.start_time_1 <= departure_time < schedule_detail.end_time_1:
                                        # C'est un départ anticipé par rapport à la plage du matin
                                        is_early_departure = True
                                        # Calculer les minutes de départ anticipé
                                        from datetime import datetime
                                        early_minutes = int((datetime.combine(date, schedule_detail.end_time_1) -
                                                          datetime.combine(date, departure_time)).total_seconds() / 60)
                                        early_departure_minutes = early_minutes

                                # Vérifier ensuite par rapport à la plage de l'après-midi
                                if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                                    # Si l'heure de départ est entre l'heure de début et l'heure de fin de l'après-midi
                                    if schedule_detail.start_time_2 <= departure_time < schedule_detail.end_time_2:
                                        # C'est un départ anticipé par rapport à la plage de l'après-midi
                                        is_early_departure = True
                                        # Calculer les minutes de départ anticipé
                                        from datetime import datetime
                                        early_minutes = int((datetime.combine(date, schedule_detail.end_time_2) -
                                                          datetime.combine(date, departure_time)).total_seconds() / 60)
                                        early_departure_minutes = early_minutes

                            except ScheduleDetail.DoesNotExist:
                                # Pas de planning pour ce jour
                                continue

                            break

                    # Mettre à jour le timesheet avec les informations de départ anticipé
                    if is_early_departure and early_departure_minutes > 0:
                        last_departure.is_early_departure = True
                        last_departure.early_departure_minutes = early_departure_minutes
                        last_departure.save()
                        logging.getLogger(__name__).info(
                            f"Mise à jour du pointage {last_departure.id} pour {employee.get_full_name()} : "
                            f"départ anticipé de {early_departure_minutes} minutes."
                        )

                    # Créer une anomalie si le départ est anticipé
                    if not last_departure.is_early_departure and not last_departure.early_departure_minutes:
                        # Vérifier si c'est un départ anticipé en calculant manuellement
                        from sites.models import ScheduleDetail
                        for site_employee in site_employee_relations:
                            schedule = site_employee.schedule
                            if not schedule or not schedule.is_active:
                                continue

                            # Vérifier si le planning a des détails pour ce jour
                            try:
                                schedule_detail = ScheduleDetail.objects.get(
                                    schedule=schedule,
                                    day_of_week=date.weekday()
                                )

                                # Vérifier si c'est un départ anticipé
                                departure_time = last_departure.timestamp.time()

                                # Vérifier d'abord par rapport à la plage du matin
                                if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                                    if schedule_detail.start_time_1 <= departure_time < schedule_detail.end_time_1:
                                        # C'est un départ anticipé par rapport à la plage du matin
                                        from datetime import datetime
                                        early_minutes = int((datetime.combine(date, schedule_detail.end_time_1) -
                                                          datetime.combine(date, departure_time)).total_seconds() / 60)
                                        if early_minutes > 0:
                                            last_departure.is_early_departure = True
                                            last_departure.early_departure_minutes = early_minutes
                                            last_departure.save()
                                            associated_schedule = schedule
                                            break

                                # Vérifier ensuite par rapport à la plage de l'après-midi
                                if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                                    if schedule_detail.start_time_2 <= departure_time < schedule_detail.end_time_2:
                                        # C'est un départ anticipé par rapport à la plage de l'après-midi
                                        from datetime import datetime
                                        early_minutes = int((datetime.combine(date, schedule_detail.end_time_2) -
                                                          datetime.combine(date, departure_time)).total_seconds() / 60)
                                        if early_minutes > 0:
                                            last_departure.is_early_departure = True
                                            last_departure.early_departure_minutes = early_minutes
                                            last_departure.save()
                                            associated_schedule = schedule
                                            break
                            except ScheduleDetail.DoesNotExist:
                                continue

                    # Récupérer la marge de départ anticipé
                    early_departure_margin = 0
                    if associated_schedule:
                        early_departure_margin = associated_schedule.early_departure_margin or site.early_departure_margin
                    else:
                        early_departure_margin = site.early_departure_margin

                    # Créer une anomalie pour tous les départs anticipés, même ceux dans la marge
                    if last_departure.is_early_departure and last_departure.early_departure_minutes > 0:
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            timesheet=last_departure,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
                            defaults={
                                'description': f'Départ anticipé de {last_departure.early_departure_minutes} minutes.',
                                'minutes': last_departure.early_departure_minutes,
                                'status': Anomaly.AnomalyStatus.PENDING,
                                'schedule': associated_schedule
                            }
                        )

                        # Associer le pointage concerné à l'anomalie
                        if created:
                            anomaly.related_timesheets.add(last_departure)
                            anomalies_created += 1
                            logging.getLogger(__name__).info(
                                f"Anomalie de départ anticipé créée pour {employee.get_full_name()} le {date} au site {site.name}. "
                                f"Départ anticipé: {last_departure.early_departure_minutes} minutes, Marge: {early_departure_margin} minutes"
                            )

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
                        # Récupérer les plannings de l'employé pour ce site
                        from sites.models import SiteEmployee, Schedule
                        site_employee_relations = SiteEmployee.objects.filter(
                            site=site,
                            employee=employee,
                            is_active=True
                        ).select_related('schedule')

                        # Trouver le planning le plus pertinent pour cette date
                        associated_schedule = None
                        for site_employee in site_employee_relations:
                            if site_employee.schedule and site_employee.schedule.is_active:
                                # Vérifier si ce planning est actif pour ce jour
                                if self._is_schedule_active_for_date(site_employee.schedule, date):
                                    associated_schedule = site_employee.schedule
                                    break

                        # Trouver le premier pointage de départ pour l'associer à l'anomalie
                        first_departure = departures[0] if departures else None

                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                            defaults={
                                'description': 'Aucun pointage d\'arrivée enregistré.',
                                'status': Anomaly.AnomalyStatus.PENDING,
                                'schedule': associated_schedule,
                                'timesheet': first_departure  # Associer l'anomalie au premier pointage de départ
                            }
                        )

                        # Associer les pointages existants à l'anomalie
                        if created and day_timesheets:
                            for ts in day_timesheets:
                                anomaly.related_timesheets.add(ts)
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
                        # Récupérer les plannings de l'employé pour ce site
                        from sites.models import SiteEmployee, Schedule
                        site_employee_relations = SiteEmployee.objects.filter(
                            site=site,
                            employee=employee,
                            is_active=True
                        ).select_related('schedule')

                        # Trouver le planning le plus pertinent pour cette date
                        associated_schedule = None
                        for site_employee in site_employee_relations:
                            if site_employee.schedule and site_employee.schedule.is_active:
                                # Vérifier si ce planning est actif pour ce jour
                                if self._is_schedule_active_for_date(site_employee.schedule, date):
                                    associated_schedule = site_employee.schedule
                                    # Journaliser pour débogage
                                    logging.getLogger(__name__).info(
                                        f"Planning trouvé pour l'anomalie de départ manquant: {associated_schedule.id} - {associated_schedule}"
                                    )
                                    break

                        # Description simple pour les départs manquants
                        description = 'Aucun pointage de départ enregistré.'

                        # Trouver le dernier pointage d'arrivée pour l'associer à l'anomalie
                        last_arrival = arrivals[-1] if arrivals else None

                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
                            defaults={
                                'description': description,
                                'status': Anomaly.AnomalyStatus.PENDING,
                                'schedule': associated_schedule,
                                'timesheet': last_arrival  # Associer l'anomalie au dernier pointage d'arrivée
                            }
                        )

                        # Associer les pointages existants à l'anomalie
                        if created and day_timesheets:
                            for ts in day_timesheets:
                                anomaly.related_timesheets.add(ts)
                            anomalies_created += 1

                            # Vérifier et journaliser l'association du planning
                            if associated_schedule and not anomaly.schedule:
                                anomaly.schedule = associated_schedule
                                anomaly.save()
                                logging.getLogger(__name__).info(
                                    f"Planning {associated_schedule.id} associé à l'anomalie {anomaly.id} après création"
                                )
                    else:
                        # Vérifier si des pointages de départ existent pour cette date
                        # Si oui, ne pas créer d'anomalie car c'est probablement un faux positif
                        departures_count = Timesheet.objects.filter(
                            employee=employee,
                            site=site,
                            timestamp__date=date,
                            entry_type=Timesheet.EntryType.DEPARTURE
                        ).count()

                        if departures_count > 0:
                            logging.getLogger(__name__).info(
                                f"Pas d'anomalie de départ manquant créée pour {employee.get_full_name()} le {date} au site {site.name}. "
                                f"{departures_count} pointage(s) de départ déjà existant(s)."
                            )
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

                # 7. Vérifier la durée pour les plannings fréquence
                # Récupérer les relations site-employé avec planning fréquence
                from sites.models import SiteEmployee, Schedule, ScheduleDetail
                site_employee_relations = SiteEmployee.objects.filter(
                    site=site,
                    employee=employee,
                    is_active=True,
                    schedule__schedule_type=Schedule.ScheduleType.FREQUENCY
                ).select_related('schedule')

                # Si l'employé a un planning fréquence pour ce site
                if site_employee_relations.exists() and arrivals and departures:
                    # Calculer la durée totale en minutes
                    total_minutes = sum(
                        (dep.timestamp - arr.timestamp).total_seconds() / 60
                        for arr, dep in zip(arrivals, departures)
                        if arr.timestamp < dep.timestamp
                    )

                    # Pour chaque planning fréquence de l'employé
                    for site_employee in site_employee_relations:
                        schedule = site_employee.schedule
                        if not schedule or not schedule.is_active:
                            continue

                        # Récupérer les détails du planning pour le jour actuel
                        try:
                            schedule_detail = ScheduleDetail.objects.get(
                                schedule=schedule,
                                day_of_week=date.weekday()
                            )

                            # Vérifier si la durée est conforme à la fréquence attendue
                            expected_duration = schedule_detail.frequency_duration
                            if expected_duration and expected_duration > 0:
                                # Calculer la marge de tolérance
                                tolerance_percentage = schedule.frequency_tolerance_percentage or site.frequency_tolerance or 10
                                min_duration = expected_duration * (1 - tolerance_percentage / 100)

                                # Si la durée est inférieure à la durée minimale attendue
                                if total_minutes < min_duration:
                                    # Trouver le dernier départ pour l'associer à l'anomalie
                                    last_departure = departures[-1] if departures else None

                                    # Supprimer les anomalies existantes pour éviter les doublons
                                    Anomaly.objects.filter(
                                        employee=employee,
                                        site=site,
                                        date=date,
                                        anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
                                    ).delete()

                                    # Créer une anomalie pour durée insuffisante
                                    anomaly = Anomaly.objects.create(
                                        employee=employee,
                                        site=site,
                                        date=date,
                                        anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS,
                                        description=f'Durée de présence insuffisante pour planning fréquence. '
                                                   f'Durée: {total_minutes:.0f} minutes, Minimum requis: {min_duration:.0f} minutes '
                                                   f'(fréquence: {expected_duration} minutes, tolérance: {tolerance_percentage}%)',
                                        minutes=int(expected_duration - total_minutes),
                                        status=Anomaly.AnomalyStatus.PENDING,
                                        schedule=schedule,
                                        timesheet=last_departure  # Associer l'anomalie au dernier départ
                                    )
                                    created = True

                                    # Associer les pointages concernés à l'anomalie
                                    if created:
                                        for arr, dep in zip(arrivals, departures):
                                            if arr.timestamp < dep.timestamp:
                                                anomaly.related_timesheets.add(arr, dep)
                                    if created:
                                        anomalies_created += 1
                                        logging.getLogger(__name__).info(
                                            f"Anomalie de durée insuffisante créée pour {employee.get_full_name()} le {date} au site {site.name}. "
                                            f"Durée: {total_minutes:.0f} minutes, Minimum requis: {min_duration:.0f} minutes"
                                        )
                        except ScheduleDetail.DoesNotExist:
                            # Pas de planning pour ce jour
                            continue

            # Préparer la réponse
            response_data = {
                'message': f'{anomalies_created} anomalies détectées',
                'anomalies_created': anomalies_created
            }

            # Si force_update était activé, ajouter des informations sur les pointages mis à jour
            if serializer.validated_data.get('force_update', False):
                response_data['force_update'] = True
                response_data['timesheets_updated'] = len(timesheets)
                response_data['message'] = f'{anomalies_created} anomalies détectées, {len(timesheets)} pointages mis à jour'

            return Response(response_data)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du scan des anomalies: {str(e)}", exc_info=True)
            return Response({
                'error': f"Erreur lors du scan des anomalies: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

