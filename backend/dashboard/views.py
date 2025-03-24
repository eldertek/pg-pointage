from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, time
from sites.models import Site
from users.models import User
from timesheets.models import Timesheet
from alerts.models import Alert
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    """
    Get dashboard statistics including:
    - Total active sites
    - Total active employees
    - Today's timesheet count
    - Current unresolved anomalies count
    """
    try:
        logger.info("Fetching dashboard statistics")
        
        # Get today's date range
        today = timezone.now().date()
        today_start = datetime.combine(today, time.min)
        today_end = datetime.combine(today, time.max)
        
        # Get stats based on user's organization
        organization = request.user.organization
        
        stats = {
            'sitesCount': Site.objects.filter(organization=organization, is_active=True).count(),
            'employeesCount': User.objects.filter(organization=organization, is_active=True).count(),
            'timesheetsCount': Timesheet.objects.filter(
                site__organization=organization,
                created_at__range=(today_start, today_end)
            ).count(),
            'anomaliesCount': Alert.objects.filter(
                site__organization=organization,
                status='pending'
            ).count()
        }
        
        logger.info(f"Dashboard stats retrieved: {stats}")
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return Response(
            {'error': 'Une erreur est survenue lors du chargement des statistiques'},
            status=500
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_anomalies(request):
    """
    Get the 10 most recent anomalies for the organization
    """
    try:
        logger.info("Fetching recent anomalies")
        
        organization = request.user.organization
        recent_anomalies = Alert.objects.filter(
            site__organization=organization
        ).order_by('-created_at')[:10].values(
            'id',
            'type',
            'employee__first_name',
            'employee__last_name',
            'site__name',
            'created_at',
            'status'
        )
        
        # Format the response
        formatted_anomalies = [{
            'id': anomaly['id'],
            'type': anomaly['type'],
            'employee': f"{anomaly['employee__first_name']} {anomaly['employee__last_name']}",
            'site': anomaly['site__name'],
            'created_at': anomaly['created_at'].isoformat(),
            'status': anomaly['status']
        } for anomaly in recent_anomalies]
        
        logger.info(f"Retrieved {len(formatted_anomalies)} recent anomalies")
        return Response(formatted_anomalies)
        
    except Exception as e:
        logger.error(f"Error fetching recent anomalies: {str(e)}")
        return Response(
            {'error': 'Une erreur est survenue lors du chargement des anomalies'},
            status=500
        ) 