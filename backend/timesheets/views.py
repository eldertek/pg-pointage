from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from .models import Timesheet, Anomaly, EmployeeReport
from .serializers import (
    TimesheetSerializer, TimesheetCreateSerializer,
    AnomalySerializer, EmployeeReportSerializer
)
from sites.permissions import IsSiteOrganizationManager
from rest_framework.permissions import BasePermission
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

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

class TimesheetListView(generics.ListAPIView):
    """Vue pour lister les pointages"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):  # Handling swagger generation
            return Timesheet.objects.none()
            
        if user.is_super_admin:
            return Timesheet.objects.all()
        elif user.is_manager and user.organization:
            return Timesheet.objects.filter(site__organization=user.organization)
        else:
            return Timesheet.objects.filter(employee=user)

class TimesheetDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour obtenir et mettre à jour un pointage"""
    serializer_class = TimesheetSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):  # Handling swagger generation
            return Timesheet.objects.none()
            
        if user.is_super_admin:
            return Timesheet.objects.all()
        elif user.is_manager and user.organization:
            return Timesheet.objects.filter(site__organization=user.organization)
        else:
            return Timesheet.objects.filter(employee=user)

class TimesheetCreateView(generics.CreateAPIView):
    """Vue pour créer un pointage via l'application mobile"""
    serializer_class = TimesheetCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        try:
            serializer.save(employee=self.request.user)
        except ValidationError as e:
            error_messages = {}
            if hasattr(e, 'message_dict'):
                error_messages = e.message_dict
            else:
                error_messages = {'non_field_errors': [str(e)]}
            raise serializers.ValidationError(error_messages)

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return response
        except serializers.ValidationError as e:
            return Response(
                {'detail': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AnomalyListView(generics.ListAPIView):
    """Vue pour lister les anomalies"""
    serializer_class = AnomalySerializer
    
    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        if not self.request.method in permissions.SAFE_METHODS:
            permission_classes = [IsAdminOrManager]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):  # Handling swagger generation
            return Anomaly.objects.none()
            
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_manager and user.organization:
            return Anomaly.objects.filter(site__organization=user.organization)
        else:
            return Anomaly.objects.filter(employee=user)

class AnomalyDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour obtenir et mettre à jour une anomalie"""
    serializer_class = AnomalySerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):  # Handling swagger generation
            return Anomaly.objects.none()
            
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_manager and user.organization:
            return Anomaly.objects.filter(site__organization=user.organization)
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
                return (timesheet.employee_id, timesheet.site_id, timesheet.timestamp.date())
            
            # Trier les pointages pour le groupby
            sorted_timesheets = sorted(timesheets, key=get_date_key)
            
            # Parcourir les pointages groupés par employé, site et date
            for (employee_id, site_id, date), day_timesheets in groupby(sorted_timesheets, get_date_key):
                day_timesheets = list(day_timesheets)
                if not day_timesheets:
                    continue
                
                employee = day_timesheets[0].employee
                site = day_timesheets[0].site
                
                # 1. Vérifier les pointages consécutifs du même type
                last_type = None
                for ts in day_timesheets:
                    if last_type == ts.entry_type:
                        anomaly, created = Anomaly.objects.get_or_create(
                            employee=employee,
                            site=site,
                            timesheet=ts,
                            date=date,
                            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE,
                            defaults={
                                'description': f'Pointage {ts.get_entry_type_display()} consécutif détecté.',
                                'status': Anomaly.AnomalyStatus.PENDING
                            }
                        )
                        if created:
                            anomalies_created += 1
                    last_type = ts.entry_type
                
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
                if not arrivals:
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
                
                # 5. Vérifier les départs manquants
                if not departures:
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du scan des anomalies: {str(e)}", exc_info=True)
            return Response({
                'error': f"Erreur lors du scan des anomalies: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

