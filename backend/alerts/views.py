from rest_framework import generics, permissions
from rest_framework.permissions import BasePermission
from .models import Alert
from .serializers import AlertSerializer
from sites.permissions import IsSiteOrganizationManager
from django.db import models

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

class AlertListView(generics.ListCreateAPIView):
    """Vue pour lister toutes les alertes et en créer de nouvelles"""
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Alert.objects.all()
        elif user.is_admin or user.is_manager:
            return Alert.objects.filter(site__organization__in=user.organizations.all())
        else:
            return Alert.objects.filter(employee=user)

class AlertDetailView(generics.RetrieveUpdateAPIView):
    """Vue pour obtenir et mettre à jour une alerte"""
    serializer_class = AlertSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Alert.objects.all()
        elif user.is_admin or user.is_manager:
            return Alert.objects.filter(site__organization__in=user.organizations.all())
        else:
            return Alert.objects.filter(employee=user)

