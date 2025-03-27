from rest_framework import generics, permissions
from rest_framework.permissions import BasePermission
from .models import Alert
from .serializers import AlertSerializer
from sites.permissions import IsSiteOrganizationManager

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

class AlertListView(generics.ListAPIView):
    """Vue pour lister les alertes"""
    serializer_class = AlertSerializer
    
    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        if not self.request.method in permissions.SAFE_METHODS:
            permission_classes = [IsAdminOrManager]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):  # Handling swagger generation
            return Alert.objects.none()
            
        if user.is_super_admin:
            return Alert.objects.all()
        elif user.is_manager and user.organization:
            return Alert.objects.filter(site__organization=user.organization)
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
        elif user.is_manager and user.organization:
            return Alert.objects.filter(site__organization=user.organization)
        else:
            return Alert.objects.filter(employee=user)

