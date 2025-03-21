from rest_framework import generics, permissions
from .models import Alert
from .serializers import AlertSerializer
from sites.permissions import IsSiteOrganizationManager

class AlertListView(generics.ListAPIView):
    """Vue pour lister les alertes"""
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
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
        return [permissions.IsAdminUser() | IsSiteOrganizationManager()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Alert.objects.all()
        elif user.is_manager and user.organization:
            return Alert.objects.filter(site__organization=user.organization)
        else:
            return Alert.objects.filter(employee=user)

