from rest_framework.views import APIView
from rest_framework import permissions, serializers
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from sites.models import Site
from users.models import User
from timesheets.models import Timesheet, Anomaly
from timesheets.serializers import AnomalySerializer
from drf_spectacular.utils import extend_schema
import logging

logger = logging.getLogger(__name__)

class DashboardStatsSerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    total_sites = serializers.IntegerField()
    active_sites = serializers.IntegerField()
    pending_anomalies = serializers.IntegerField()

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={200: DashboardStatsSerializer},
        description="Obtenir les statistiques du tableau de bord"
    )
    def get(self, request):
        user = request.user
        
        if user.is_super_admin:
            total_employees = User.objects.filter(is_active=True).count()
            total_sites = Site.objects.all().count()
            active_sites = Site.objects.filter(is_active=True).count()
            pending_anomalies = Anomaly.objects.filter(status='PENDING').count()
        elif user.is_manager and user.organization:
            total_employees = User.objects.filter(
                organization=user.organization,
                is_active=True
            ).count()
            total_sites = Site.objects.filter(
                organization=user.organization
            ).count()
            active_sites = Site.objects.filter(
                organization=user.organization,
                is_active=True
            ).count()
            pending_anomalies = Anomaly.objects.filter(
                site__organization=user.organization,
                status='PENDING'
            ).count()
        else:
            total_employees = 1
            total_sites = user.assigned_sites.count()
            active_sites = user.assigned_sites.filter(is_active=True).count()
            pending_anomalies = Anomaly.objects.filter(
                employee=user,
                status='PENDING'
            ).count()
        
        stats = {
            'total_employees': total_employees,
            'total_sites': total_sites,
            'active_sites': active_sites,
            'pending_anomalies': pending_anomalies
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

class RecentAnomaliesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={200: AnomalySerializer(many=True)},
        description="Obtenir les anomalies récentes"
    )
    def get(self, request):
        user = request.user
        
        # Récupérer les anomalies des 7 derniers jours
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        if user.is_super_admin:
            anomalies = Anomaly.objects.filter(
                created_at__gte=seven_days_ago
            )
        elif user.is_manager and user.organization:
            anomalies = Anomaly.objects.filter(
                site__organization=user.organization,
                created_at__gte=seven_days_ago
            )
        else:
            anomalies = Anomaly.objects.filter(
                employee=user,
                created_at__gte=seven_days_ago
            )
        
        # Limiter à 10 anomalies
        anomalies = anomalies.order_by('-created_at')[:10]
        serializer = AnomalySerializer(anomalies, many=True)
        return Response(serializer.data) 