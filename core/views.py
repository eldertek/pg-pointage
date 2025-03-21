from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.shortcuts import redirect
from django.contrib.auth.models import Group

from .models import (
    User, Site, Planning, Pointage, Anomalie, StatistiquesTemps
)
from .serializers import (
    UserSerializer, GroupSerializer, SiteSerializer, PlanningSerializer,
    PointageSerializer, AnomalieSerializer, StatistiquesTempsSerializer
)
from .utils.logging import log_user_action
import logging

logger = logging.getLogger(__name__)

class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all API endpoints.
    Implements common functionality like filtering by organization.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user's organization"""
        queryset = super().get_queryset()
        
        # Apply organization filter for non-superusers
        if not self.request.user.is_superuser and hasattr(queryset.model, 'organisation'):
            queryset = queryset.filter(
                Q(organisation=self.request.user.organisation) | 
                Q(organisation__isnull=True)
            )
            
        # Apply search filters
        search = self.request.query_params.get('search', None)
        if search and hasattr(self, 'search_fields') and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(q_objects)
            
        return queryset
    
    def perform_create(self, serializer):
        """Set organization when creating objects"""
        if hasattr(serializer.Meta.model, 'organisation') and self.request.user.organisation:
            serializer.save(organisation=self.request.user.organisation)
        else:
            serializer.save()

class UserViewSet(BaseModelViewSet):
    """API endpoint for managing users."""
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self):
        """Filter users based on role and organization"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
        elif user.role == 'manager' and user.organisation:
            return queryset.filter(organisation=user.organisation)
        return queryset.filter(id=user.id)
    
    @action(detail=False)
    def me(self, request):
        """Return current user info"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False)
    def gardiens(self, request):
        """Return all security guards"""
        queryset = self.get_queryset().filter(role='gardien')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def agents_nettoyage(self, request):
        """Return all cleaning staff"""
        queryset = self.get_queryset().filter(role='agent_de_nettoyage')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class GroupViewSet(BaseModelViewSet):
    """API endpoint for managing organizations."""
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    search_fields = ['name']
    
    def get_permissions(self):
        """Only superadmins can manage organizations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class SiteViewSet(BaseModelViewSet):
    """API endpoint for managing sites."""
    queryset = Site.objects.all().order_by('name')
    serializer_class = SiteSerializer
    search_fields = ['name', 'adresse', 'qr_code_value']
    
    @action(detail=True)
    def plannings(self, request, pk=None):
        """Return site plannings"""
        site = self.get_object()
        plannings = Planning.objects.filter(site=site)
        if not request.user.is_superuser:
            plannings = plannings.filter(organisation=request.user.organisation)
        serializer = PlanningSerializer(plannings, many=True)
        return Response(serializer.data)
    
    @action(detail=True)
    def verify_qr(self, request, pk=None):
        """Verify QR code"""
        site = self.get_object()
        qr_value = request.query_params.get('qr_value', None)
        
        if not qr_value:
            return Response(
                {"detail": "QR code value is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if site.qr_code_value == qr_value:
            return Response({"valid": True, "site_id": site.id})
        return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND)

class PlanningViewSet(BaseModelViewSet):
    """API endpoint for managing schedules."""
    queryset = Planning.objects.all().order_by('-actif', 'site__name')
    serializer_class = PlanningSerializer
    search_fields = ['site__name', 'user__username']
    
    @action(detail=False)
    def user_plannings(self, request):
        """Return user's plannings"""
        queryset = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def active(self, request):
        """Return active plannings"""
        queryset = self.get_queryset().filter(actif=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle planning active status"""
        planning = self.get_object()
        planning.actif = not planning.actif
        planning.save()
        serializer = self.get_serializer(planning)
        return Response(serializer.data)

class PointageViewSet(BaseModelViewSet):
    """API endpoint for managing time tracking."""
    queryset = Pointage.objects.all().order_by('-date_scan')
    serializer_class = PointageSerializer
    
    def get_queryset(self):
        """Filter pointages"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_superuser and self.request.user.role != 'manager':
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    @action(detail=False)
    def today(self, request):
        """Return today's pointages"""
        today = timezone.localtime().date()
        queryset = self.get_queryset().filter(date_scan__date=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def my_pointages(self, request):
        """Return user's pointages"""
        queryset = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def scan_qr(self, request):
        """Create pointage from QR scan"""
        qr_value = request.data.get('qr_value')
        type_pointage = request.data.get('type_pointage', 'ENTREE')
        
        try:
            site = Site.objects.get(qr_code_value=qr_value)
            pointage = Pointage.objects.create(
                user=request.user,
                site=site,
                date_scan=timezone.now(),
                type_pointage=type_pointage,
                organisation=request.user.organisation
            )
            pointage.trouver_planning_associe()
            pointage.save()
            pointage.creer_anomalie_si_necessaire()
            
            serializer = self.get_serializer(pointage)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Site.DoesNotExist:
            return Response(
                {"detail": "Invalid QR code"},
                status=status.HTTP_404_NOT_FOUND
            )

class AnomalieViewSet(BaseModelViewSet):
    """API endpoint for managing anomalies."""
    queryset = Anomalie.objects.all().order_by('-date_creation')
    serializer_class = AnomalieSerializer
    search_fields = ['motif', 'user__username', 'site__name']
    
    def get_queryset(self):
        """Filter anomalies"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_superuser and self.request.user.role != 'manager':
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    @action(detail=False)
    def unprocessed(self, request):
        """Return unprocessed anomalies"""
        queryset = self.get_queryset().filter(status='en_attente')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process an anomaly"""
        if not request.user.is_superuser and request.user.role != 'manager':
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        anomalie = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['justifiee', 'non_justifiee']:
            return Response(
                {"detail": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        anomalie.status = new_status
        anomalie.commentaire_traitement = request.data.get('commentaire', '')
        anomalie.date_traitement = timezone.now()
        anomalie.traite_par = request.user
        anomalie.save()
        
        serializer = self.get_serializer(anomalie)
        return Response(serializer.data)

class StatistiquesViewSet(BaseModelViewSet):
    """API endpoint for accessing statistics."""
    queryset = StatistiquesTemps.objects.all().order_by('-annee', '-mois')
    serializer_class = StatistiquesTempsSerializer
    
    def get_queryset(self):
        """Filter statistics"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_superuser and self.request.user.role != 'manager':
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    @action(detail=False)
    def my_stats(self, request):
        """Return user's statistics"""
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        queryset = self.get_queryset().filter(
            user=request.user,
            mois=month,
            annee=year
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def summary(self, request):
        """Return summary statistics"""
        if not request.user.is_superuser and request.user.role != 'manager':
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        queryset = self.get_queryset().filter(mois=month, annee=year)
        
        aggregates = queryset.aggregate(
            total_minutes_travaillees=Sum('minutes_travaillees'),
            total_minutes_retard=Sum('minutes_retard'),
            total_minutes_depart_anticipe=Sum('minutes_depart_anticipe'),
            total_minutes_absence=Sum('minutes_absence'),
            total_jours_travailles=Sum('jours_travailles'),
            count=Count('id')
        )
        
        return Response({
            'period': f"{month}/{year}",
            'hours_worked': round((aggregates['total_minutes_travaillees'] or 0) / 60, 2),
            'hours_late': round((aggregates['total_minutes_retard'] or 0) / 60, 2),
            'hours_early': round((aggregates['total_minutes_depart_anticipe'] or 0) / 60, 2),
            'hours_absent': round((aggregates['total_minutes_absence'] or 0) / 60, 2),
            'days_worked': aggregates['total_jours_travailles'] or 0,
            'user_count': aggregates['count'] or 0
        })

# Authentication views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_api(request):
    """API login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {"detail": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    user = authenticate(username=username, password=password)
    
    if not user or not user.is_active:
        log_user_action(None, 'login_failed', {'username': username})
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    refresh = RefreshToken.for_user(user)
    user.last_login = timezone.now()
    user.save()
    
    log_user_action(user, 'login', {'method': 'api'})
    
    return Response({
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'user': UserSerializer(user).data
    })

@api_view(['POST'])
def logout_api(request):
    """API logout endpoint"""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        log_user_action(request.user, 'logout', {'method': 'api'})
        return Response({"detail": "Successfully logged out"})
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response(
            {"detail": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST
        )

def home_view(request):
    """Redirect to home page"""
    return redirect('admin:index')
