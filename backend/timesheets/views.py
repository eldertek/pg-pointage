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
from django.db import models
import logging
from .utils.anomaly_processor import AnomalyProcessor

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
    pagination_class = None  # Désactiver la pagination pour cette vue

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

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Le timestamp est maintenant géré dans le serializer.validate
            timesheet = serializer.save()

            # Utiliser AnomalyProcessor pour traiter le pointage
            processor = AnomalyProcessor()
            result = processor.process_timesheet(timesheet)

            # Ajouter des logs pour déboguer
            logger = logging.getLogger(__name__)
            logger.info(f"Pointage créé: ID={timesheet.id}, Employee={timesheet.employee.id}, Site={timesheet.site.id}, "
                       f"Type={timesheet.entry_type}, Timestamp={timesheet.timestamp}, "
                       f"Est ambigu: {result.get('is_ambiguous', False)}")

            return Response({
                'message': 'Pointage enregistré avec succès',
                'data': TimesheetSerializer(timesheet).data,
                'is_ambiguous': result.get('is_ambiguous', False)
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
    pagination_class = None  # Désactiver la pagination pour cette vue

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Anomaly.objects.all()
        elif user.is_admin or user.is_manager:
            return Anomaly.objects.filter(site__organization__in=user.organizations.all())
        else:
            return Anomaly.objects.filter(employee=user)

    def filter_queryset(self, queryset):
        # Récupérer les paramètres de filtrage
        site = self.request.query_params.get('site')
        employee = self.request.query_params.get('employee')
        anomaly_type = self.request.query_params.get('anomaly_type')
        status = self.request.query_params.get('status')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        # Log pour déboguer
        logger = logging.getLogger(__name__)
        logger.info(f"Filtrage des anomalies - Paramètres: site={site}, employee={employee}, type={anomaly_type}, status={status}, start_date={start_date}, end_date={end_date}")

        # Appliquer les filtres si présents
        if site:
            queryset = queryset.filter(site_id=site)
            logger.info(f"Filtre site appliqué: {site}, résultats: {queryset.count()}")
        if employee:
            logger.info(f"[Débogage] Paramètre employé reçu dans AnomalyListView: {employee}, type: {type(employee)}")
            try:
                # Convertir en entier si ce n'est pas déjà le cas
                employee_id = int(employee)
                logger.info(f"[Débogage] ID employé converti en entier: {employee_id}")

                # Vérifier si l'employé existe
                from users.models import User
                try:
                    user = User.objects.get(id=employee_id)
                    logger.info(f"[Débogage] Employé trouvé: {user.get_full_name()} (ID: {user.id})")
                except User.DoesNotExist:
                    logger.warning(f"[Débogage] Employé avec ID {employee_id} non trouvé dans la base de données")

                # Appliquer le filtre
                queryset = queryset.filter(employee_id=employee_id)
                logger.info(f"Filtre employé appliqué: {employee_id}, résultats: {queryset.count()}")

                # Afficher les anomalies trouvées pour cet employé
                if queryset.count() > 0:
                    logger.info(f"[Débogage] Anomalies trouvées pour l'employé {employee_id}:")
                    for anomaly in queryset[:5]:  # Limiter à 5 pour éviter des logs trop longs
                        logger.info(f"  - Anomalie ID: {anomaly.id}, Type: {anomaly.anomaly_type}, Date: {anomaly.date}")
                else:
                    logger.warning(f"[Débogage] Aucune anomalie trouvée pour l'employé {employee_id}")
            except (ValueError, TypeError) as e:
                logger.error(f"[Débogage] Erreur lors de la conversion de l'ID employé: {str(e)}")
                queryset = queryset.filter(employee_id=employee)
                logger.info(f"Filtre employé appliqué sans conversion: {employee}, résultats: {queryset.count()}")
        if anomaly_type:
            queryset = queryset.filter(anomaly_type=anomaly_type)
            logger.info(f"Filtre type appliqué: {anomaly_type}, résultats: {queryset.count()}")
        if status:
            queryset = queryset.filter(status=status)
            logger.info(f"Filtre statut appliqué: {status}, résultats: {queryset.count()}")
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
            logger.info(f"Filtre date de début appliqué: {start_date}, résultats: {queryset.count()}")
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            logger.info(f"Filtre date de fin appliqué: {end_date}, résultats: {queryset.count()}")

        return queryset

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

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        processor = AnomalyProcessor()

        return processor.scan_anomalies(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            site_id=serializer.validated_data.get('site'),
            employee_id=serializer.validated_data.get('employee'),
            force_update=serializer.validated_data.get('force_update', False)
        )

