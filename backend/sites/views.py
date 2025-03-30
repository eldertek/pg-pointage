from rest_framework import generics, permissions, viewsets, serializers
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
from .serializers import (
    SiteSerializer, ScheduleSerializer, ScheduleDetailSerializer, 
    SiteEmployeeSerializer
)
from .permissions import IsSiteOrganizationManager
from django.db import models
from django.db.models import Count, Q, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractHour, ExtractMinute
from timesheets.models import Timesheet, Anomaly
from users.models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse
from datetime import timedelta

class SiteStatisticsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    total_hours = serializers.IntegerField()
    anomalies = serializers.IntegerField()

class SiteStatisticsView(generics.RetrieveAPIView):
    serializer_class = SiteStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    
    @extend_schema(
        responses={200: SiteStatisticsSerializer},
        description="Obtenir les statistiques d'un site"
    )
    def get(self, request, *args, **kwargs):
        site = self.get_object()
        
        # Calculer les statistiques
        total_employees = SiteEmployee.objects.filter(site=site, is_active=True).count()
        
        # Calculer le total des heures en utilisant les entrées/sorties
        # On groupe les pointages par paire (entrée/sortie)
        timesheets = Timesheet.objects.filter(
            site=site,
            entry_type__in=['IN', 'OUT']  # Seulement les entrées et sorties
        ).order_by('employee', 'timestamp')
        
        total_hours = 0
        current_employee = None
        entry_time = None
        
        for timesheet in timesheets:
            if timesheet.entry_type == 'IN':
                entry_time = timesheet.timestamp
                current_employee = timesheet.employee
            elif timesheet.entry_type == 'OUT' and current_employee == timesheet.employee and entry_time:
                # Calculer la durée entre l'entrée et la sortie
                duration = timesheet.timestamp - entry_time
                total_hours += duration.total_seconds() / 3600  # Convertir en heures
                entry_time = None
        
        # Calculer le nombre d'anomalies
        anomalies = Anomaly.objects.filter(
            site=site
        ).count()
        
        stats = {
            'total_employees': total_employees,
            'total_hours': int(total_hours),  # Convertir en entier pour simplifier
            'anomalies': anomalies
        }
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)

class IsAdminOrManager(BasePermission):
    """Permission composée pour autoriser les admin ou les managers d'organisation"""
    def has_permission(self, request, view):
        is_admin = IsAdminUser().has_permission(request, view)
        is_manager = IsSiteOrganizationManager().has_permission(request, view)
        return is_admin or is_manager

    def has_object_permission(self, request, view, obj):
        is_admin = IsAdminUser().has_object_permission(request, view, obj)
        is_manager = IsSiteOrganizationManager().has_object_permission(request, view, obj)
        return is_admin or is_manager

class SiteListView(generics.ListCreateAPIView):
    """Vue pour lister tous les sites et en créer de nouveaux"""
    serializer_class = SiteSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        base_queryset = Site.objects.prefetch_related(
            'schedules',
            'schedules__assigned_employees',
            'schedules__assigned_employees__employee'
        )
        
        # Récupérer le paramètre organizations de la requête
        organizations = self.request.query_params.get('organizations')
        print("[Sites][Filter] Paramètre organizations reçu:", organizations)
        
        if organizations:
            # Convertir la chaîne en liste d'IDs
            organization_ids = [int(org_id) for org_id in organizations.split(',')]
            print("[Sites][Filter] IDs des organisations:", organization_ids)
            base_queryset = base_queryset.filter(organization_id__in=organization_ids)
            print("[Sites][Count] Nombre de sites après filtre:", base_queryset.count())
        
        if user.is_super_admin:
            return base_queryset
        elif user.is_admin or user.is_manager:
            return base_queryset.filter(organization__in=user.organizations.all())
        elif user.is_employee:
            return base_queryset.filter(employees__employee=user, employees__is_active=True)
        return Site.objects.none()
    
    def perform_create(self, serializer):
        # Si l'utilisateur est un manager, associer le site à son organisation
        if self.request.user.is_manager and self.request.user.organization:
            serializer.save(
                organization=self.request.user.organization,
                manager=self.request.user  # Le manager créateur devient le manager du site
            )
        else:
            serializer.save()

class SiteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un site spécifique"""
    serializer_class = SiteSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        base_queryset = Site.objects.prefetch_related(
            'schedules',
            'schedules__assigned_employees',
            'schedules__assigned_employees__employee'
        )
        
        if user.is_super_admin:
            return base_queryset.all()
        elif user.is_admin or user.is_manager:
            return base_queryset.filter(organization__in=user.organizations.all())
        elif user.is_employee:
            return base_queryset.filter(employees__employee=user, employees__is_active=True)
        return Site.objects.none()

class ScheduleListView(generics.ListCreateAPIView):
    """Vue pour lister tous les plannings d'un site et en créer de nouveaux"""
    serializer_class = ScheduleSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return Schedule.objects.filter(site_id=site_pk)
    
    def perform_create(self, serializer):
        site_pk = self.kwargs.get('site_pk')
        serializer.save(site_id=site_pk)

class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un planning spécifique"""
    serializer_class = ScheduleSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return Schedule.objects.filter(site_id=site_pk)

class ScheduleDetailListView(generics.ListCreateAPIView):
    """Vue pour lister tous les détails d'un planning et en créer de nouveaux"""
    serializer_class = ScheduleDetailSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        schedule_pk = self.kwargs.get('schedule_pk')
        return ScheduleDetail.objects.filter(schedule_id=schedule_pk)
    
    def perform_create(self, serializer):
        schedule_pk = self.kwargs.get('schedule_pk')
        serializer.save(schedule_id=schedule_pk)

class SiteEmployeeListView(generics.ListCreateAPIView):
    """Vue pour lister tous les employés d'un site et en ajouter de nouveaux"""
    serializer_class = SiteEmployeeSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return SiteEmployee.objects.filter(site_id=site_pk)
    
    def perform_create(self, serializer):
        site_pk = self.kwargs.get('site_pk')
        serializer.save(site_id=site_pk)

class SiteEmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer un employé d'un site"""
    serializer_class = SiteEmployeeSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return SiteEmployee.objects.filter(site_id=site_pk)

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]

class GlobalScheduleListView(generics.ListCreateAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrer par site si spécifié
        site = self.request.query_params.get('site', None)
        if site is not None:
            queryset = queryset.filter(site=site)
            
        # Filtrer par type de planning si spécifié
        schedule_type = self.request.query_params.get('schedule_type', None)
        if schedule_type is not None:
            queryset = queryset.filter(schedule_type=schedule_type)
            
        return queryset

class GlobalScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

class SiteUnassignedEmployeesView(generics.ListAPIView):
    """Vue pour lister tous les employés non assignés à un site spécifique"""
    serializer_class = 'users.serializers.UserSerializer'  # On utilise le même sérialiseur que pour les organisations
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
            
        site = Site.objects.get(pk=self.kwargs['pk'])
        
        # Récupérer les employés qui :
        # 1. Sont dans la même organisation que le site
        # 2. Ne sont pas déjà assignés à ce site
        # 3. Sont actifs
        return User.objects.filter(
            organization=site.organization,
            is_active=True
        ).exclude(
            id__in=SiteEmployee.objects.filter(
                site=site,
                is_active=True
            ).values_list('employee_id', flat=True)
        ).order_by('last_name', 'first_name')

