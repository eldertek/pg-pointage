from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Q
from .models import Organization
from .serializers import OrganizationSerializer
from users.models import User
from users.serializers import UserSerializer
from sites.models import Site
from sites.serializers import SiteSerializer
from timesheets.models import Anomaly, Timesheet
from timesheets.serializers import AnomalySerializer, TimesheetSerializer
from reports.models import Report
from reports.serializers import ReportSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

class OrganizationStatisticsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    total_sites = serializers.IntegerField()
    active_sites = serializers.IntegerField()
    total_anomalies = serializers.IntegerField()
    pending_anomalies = serializers.IntegerField()

class OrganizationListView(generics.ListCreateAPIView):
    """Vue pour lister toutes les organisations et en créer de nouvelles"""
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Super Admin voit toutes les organisations
        if user.is_super_admin:
            return Organization.objects.all()

        # Les autres utilisateurs ne voient que leurs organisations
        return user.organizations.all()

class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour afficher, modifier et supprimer une organisation"""
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        # Super admin peut tout voir
        if user.is_super_admin:
            return obj

        # Les autres utilisateurs ne peuvent voir que leurs organisations
        if not user.organizations.filter(id=obj.id).exists():
            raise PermissionDenied("Vous n'avez pas accès à cette organisation")

        return obj

class OrganizationUsersView(generics.ListAPIView):
    """Vue pour lister tous les utilisateurs d'une organisation spécifique"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        organization_pk = self.kwargs.get('pk')
        return User.objects.filter(organizations__id=organization_pk)

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

        # Calculer les statistiques directement dans la vue
        total_anomalies = Anomaly.objects.filter(
            site__organization=organization
        ).count()

        pending_anomalies = Anomaly.objects.filter(
            site__organization=organization,
            status='PENDING'
        ).count()

        stats = {
            'total_employees': User.objects.filter(organizations=organization).count(),
            'total_sites': organization.sites.count(),
            'active_sites': organization.sites.filter(is_active=True).count(),
            'total_anomalies': total_anomalies,
            'pending_anomalies': pending_anomalies
        }

        serializer = self.get_serializer(stats)
        return Response(serializer.data)

class OrganizationUnassignedEmployeesView(generics.ListAPIView):
    """Vue pour lister tous les utilisateurs non assignés à une organisation spécifique"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        organization_pk = self.kwargs.get('pk')

        # Récupérer les utilisateurs qui n'appartiennent pas à cette organisation
        # et qui ont soit le rôle EMPLOYEE soit MANAGER
        role_filter = self.request.query_params.getlist('role', ['EMPLOYEE', 'MANAGER'])
        return User.objects.filter(
            ~Q(organizations__id=organization_pk),
            role__in=role_filter,
            is_active=True
        )

class OrganizationUnassignedSitesView(generics.ListAPIView):
    """Vue pour lister tous les sites non assignés à une organisation spécifique"""
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Site.objects.none()

        organization_pk = self.kwargs.get('pk')

        # Récupérer les sites qui n'appartiennent pas à cette organisation
        return Site.objects.filter(
            ~Q(organization_id=organization_pk),
            is_active=True
        )

class OrganizationSitesView(generics.ListAPIView):
    """Vue pour lister tous les sites d'une organisation spécifique"""
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Site.objects.none()

        organization_pk = self.kwargs.get('pk')

        # Récupérer uniquement les sites de cette organisation
        return Site.objects.filter(
            organization_id=organization_pk,
            is_active=True
        ).order_by('name')

@extend_schema(
    description="Assigner un site à une organisation",
    responses={200: OpenApiResponse(description="Site assigné avec succès")}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_site_to_organization(request, pk):
    """Vue pour assigner un site à une organisation"""
    try:
        organization = Organization.objects.get(pk=pk)
        site_id = request.data.get('site_id')

        if not site_id:
            return Response(
                {'error': 'L\'ID du site est requis'},
                status=400
            )

        try:
            site = Site.objects.get(pk=site_id)
        except Site.DoesNotExist:
            return Response(
                {'error': 'Site non trouvé'},
                status=404
            )

        site.organization = organization
        site.save()

        return Response(
            {'message': 'Site assigné avec succès'},
            status=200
        )

    except Organization.DoesNotExist:
        return Response(
            {'error': 'Organisation non trouvée'},
            status=404
        )

class OrganizationTimesheetsView(generics.ListAPIView):
    """Vue pour lister tous les pointages des sites d'une organisation"""
    serializer_class = TimesheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Timesheet.objects.none()

        organization_pk = self.kwargs.get('pk')
        return Timesheet.objects.filter(
            site__organization_id=organization_pk
        ).order_by('-created_at')

class OrganizationAnomaliesView(generics.ListAPIView):
    """Vue pour lister toutes les anomalies des sites d'une organisation"""
    serializer_class = AnomalySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Désactiver la pagination pour cette vue

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Anomaly.objects.none()

        organization_pk = self.kwargs.get('pk')
        return Anomaly.objects.filter(
            site__organization_id=organization_pk
        ).order_by('-created_at')

class OrganizationReportsView(generics.ListAPIView):
    """Vue pour lister tous les rapports d'une organisation"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Report.objects.none()

        organization_pk = self.kwargs.get('pk')
        return Report.objects.filter(
            site__organization_id=organization_pk
        ).order_by('-created_at')

class OrganizationEmployeesView(generics.ListAPIView):
    """Vue pour lister tous les employés d'une organisation avec filtrage optionnel par rôle"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        organization_pk = self.kwargs.get('pk')
        queryset = User.objects.filter(
            organizations__id=organization_pk,
            is_active=True
        )

        # Filtrer par rôle si spécifié
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        return queryset.order_by('last_name', 'first_name')

