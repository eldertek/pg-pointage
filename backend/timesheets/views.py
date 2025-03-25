from rest_framework import generics, permissions, status
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

class TimesheetListView(generics.ListAPIView):
    """Vue pour lister les pointages"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Timesheet.objects.all()
        elif user.is_manager and user.organization:
            return Timesheet.objects.filter(site__organization=user.organization)
        else:
            return Timesheet.objects.filter(employee=user)

class TimesheetDetailView(generics.RetrieveAPIView):
    """Vue pour obtenir les détails d'un pointage"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
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

class AnomalyListView(generics.ListCreateAPIView):
    """Vue pour lister les anomalies et en créer de nouvelles"""
    serializer_class = AnomalySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
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
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        user = self.request.user
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

class ReportGenerateView(APIView):
    """Vue pour générer un rapport"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Logique de génération de rapport
        # À implémenter en fonction des besoins
        return Response({"message": "Génération de rapport lancée"}, status=status.HTTP_202_ACCEPTED)

class ScanAnomaliesView(APIView):
    """Vue pour scanner les anomalies dans les pointages existants"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Récupérer les paramètres de filtrage
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            site_id = request.data.get('site')
            employee_id = request.data.get('employee')
            
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
                'message': f'{anomalies_created} anomalies détectées et créées.',
                'anomalies_count': anomalies_created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du scan des anomalies: {str(e)}", exc_info=True)
            return Response({
                'error': f"Erreur lors du scan des anomalies: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

