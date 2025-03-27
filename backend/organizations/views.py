from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Q
from .models import Organization
from .serializers import OrganizationSerializer
from users.models import User
from users.serializers import UserSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse

class OrganizationStatisticsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    total_sites = serializers.IntegerField()
    active_sites = serializers.IntegerField()
    total_anomalies = serializers.IntegerField()
    pending_anomalies = serializers.IntegerField()

class OrganizationListView(generics.ListCreateAPIView):
    """Vue pour lister toutes les organisations et en créer de nouvelles"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer une organisation spécifique"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrganizationUsersView(generics.ListAPIView):
    """Vue pour lister tous les utilisateurs d'une organisation spécifique"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
            
        organization_pk = self.kwargs.get('pk')
        return User.objects.filter(organization_id=organization_pk)

class OrganizationStatisticsView(generics.RetrieveAPIView):
    serializer_class = OrganizationStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()
    
    @extend_schema(
        responses={200: OrganizationStatisticsSerializer},
        description="Obtenir les statistiques d'une organisation"
    )
    def get(self, request, *args, **kwargs):
        organization = self.get_object()
        
        stats = {
            'total_employees': organization.users.count(),
            'total_sites': organization.sites.count(),
            'active_sites': organization.sites.filter(is_active=True).count(),
            'total_anomalies': organization.get_total_anomalies(),
            'pending_anomalies': organization.get_pending_anomalies()
        }
        
        serializer = self.get_serializer(stats)
        return Response(serializer.data)

