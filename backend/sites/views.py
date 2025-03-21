from rest_framework import generics, permissions
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
from .serializers import (
    SiteSerializer, ScheduleSerializer, ScheduleDetailSerializer, 
    SiteEmployeeSerializer
)
from .permissions import IsSiteOrganizationManager

class SiteListView(generics.ListCreateAPIView):
    """Vue pour lister tous les sites et en créer de nouveaux"""
    serializer_class = SiteSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        user = self.request.user
        # Super admin voit tous les sites
        if user.is_super_admin:
            return Site.objects.all()
        # Manager voit les sites de son organisation
        elif user.is_manager and user.organization:
            return Site.objects.filter(organization=user.organization)
        # Employé voit les sites auxquels il est assigné
        elif user.is_employee:
            return Site.objects.filter(employees__employee=user, employees__is_active=True)
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
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Site.objects.all()
        elif user.is_manager and user.organization:
            return Site.objects.filter(organization=user.organization)
        elif user.is_employee:
            return Site.objects.filter(employees__employee=user, employees__is_active=True)
        return Site.objects.none()

class ScheduleListView(generics.ListCreateAPIView):
    """Vue pour lister tous les plannings d'un site et en créer de nouveaux"""
    serializer_class = ScheduleSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
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
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return Schedule.objects.filter(site_id=site_pk)

class ScheduleDetailListView(generics.ListCreateAPIView):
    """Vue pour lister tous les détails d'un planning et en créer de nouveaux"""
    serializer_class = ScheduleDetailSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
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
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
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
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        site_pk = self.kwargs.get('site_pk')
        return SiteEmployee.objects.filter(site_id=site_pk)

