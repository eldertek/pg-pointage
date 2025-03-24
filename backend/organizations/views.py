from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Q
from .models import Organization
from .serializers import OrganizationSerializer
from users.serializers import UserSerializer

class OrganizationListView(generics.ListCreateAPIView):
    """Vue pour lister toutes les organisations et en créer de nouvelles"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour obtenir, mettre à jour et supprimer une organisation spécifique"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

class OrganizationUsersView(generics.ListAPIView):
    """Vue pour lister tous les utilisateurs d'une organisation spécifique"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        organization_id = self.kwargs['pk']
        user = self.request.user
        
        # Si l'utilisateur est un super admin ou appartient à cette organisation
        if user.is_super_admin or (user.organization and user.organization.id == organization_id):
            return user.__class__.objects.filter(organization_id=organization_id)
        
        return user.__class__.objects.none()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def organization_statistics(request, pk):
    """Vue pour obtenir les statistiques d'une organisation"""
    try:
        organization = Organization.objects.get(pk=pk)
        users = organization.users.all()
        
        stats = {
            'sites': organization.sites.count(),
            'employees': users.filter(role='EMPLOYEE').count(),
            'managers': users.filter(role='MANAGER').count()
        }
        
        return Response(stats)
    except Organization.DoesNotExist:
        return Response({'error': 'Organisation non trouvée'}, status=404)

