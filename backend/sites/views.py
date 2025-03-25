from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
from .serializers import (
    SiteSerializer, ScheduleSerializer, ScheduleDetailSerializer, 
    SiteEmployeeSerializer
)
from .permissions import IsSiteOrganizationManager

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
        # Super admin voit tous les sites
        if user.is_super_admin:
            return Site.objects.prefetch_related(
                'schedules',
                'schedules__assigned_employees',
                'schedules__assigned_employees__employee'
            ).all()
        # Manager voit les sites de son organisation
        elif user.is_manager and user.organization:
            return Site.objects.prefetch_related(
                'schedules',
                'schedules__assigned_employees',
                'schedules__assigned_employees__employee'
            ).filter(organization=user.organization)
        # Employé voit les sites auxquels il est assigné
        elif user.is_employee:
            return Site.objects.prefetch_related(
                'schedules',
                'schedules__assigned_employees',
                'schedules__assigned_employees__employee'
            ).filter(employees__employee=user, employees__is_active=True)
        return Site.objects.none()
    
    def perform_create(self, serializer):
        # Si l'utilisateur est un manager, associer le site à son organisation
        if self.request.user.is_manager and self.request.user.organization:
            serializer.save(organization=self.request.user.organization)
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
        if user.is_super_admin:
            return Site.objects.prefetch_related(
                'schedules',
                'schedules__assigned_employees',
                'schedules__assigned_employees__employee'
            ).all()
        elif user.is_manager and user.organization:
            return Site.objects.prefetch_related(
                'schedules',
                'schedules__assigned_employees',
                'schedules__assigned_employees__employee'
            ).filter(organization=user.organization)
        elif user.is_employee:
            return Site.objects.prefetch_related(
                'schedules',
                'schedules__assigned_employees',
                'schedules__assigned_employees__employee'
            ).filter(employees__employee=user, employees__is_active=True)
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

class ScheduleEmployeeListView(generics.ListCreateAPIView):
    """Vue pour lister et assigner des employés à un planning"""
    serializer_class = SiteEmployeeSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        schedule_pk = self.kwargs.get('schedule_pk')
        return SiteEmployee.objects.filter(
            site_id=site_pk,
            schedule_id=schedule_pk
        )
    
    def perform_create(self, serializer):
        import logging
        logger = logging.getLogger(__name__)
        
        site_pk = self.kwargs.get('site_pk')
        schedule_pk = self.kwargs.get('schedule_pk')
        employee_id = self.request.data.get('employee')
        
        if not employee_id:
            logger.error("employee manquant dans la requête")
            raise serializers.ValidationError({"employee": "Ce champ est obligatoire."})
        
        try:
            # Vérifier si l'employé est déjà assigné à ce planning
            existing_assignment = SiteEmployee.objects.filter(
                site_id=site_pk,
                employee_id=employee_id,
                schedule_id=schedule_pk,
                is_active=True
            ).first()
            
            if existing_assignment:
                logger.info(f"L'employé {employee_id} est déjà assigné à ce planning")
                serializer.instance = existing_assignment
                return
            
            # Désactiver toute autre assignation active de l'employé pour ce site
            SiteEmployee.objects.filter(
                site_id=site_pk,
                employee_id=employee_id,
                is_active=True
            ).update(is_active=False)
            
            # Créer une nouvelle assignation
            logger.info(f"Création d'une nouvelle assignation pour l'employé {employee_id}")
            instance = serializer.save(
                site_id=site_pk,
                employee_id=employee_id,
                schedule_id=schedule_pk,
                is_active=True
            )
            logger.info("Nouvelle assignation créée avec succès")
            return instance
            
        except Exception as e:
            logger.error(f"Erreur lors de l'assignation: {str(e)}")
            raise

class ScheduleEmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour gérer un employé spécifique d'un planning"""
    serializer_class = SiteEmployeeSerializer
    
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        schedule_pk = self.kwargs.get('schedule_pk')
        return SiteEmployee.objects.filter(
            site_id=site_pk,
            schedule_id=schedule_pk
        )

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAdminOrManager()]

