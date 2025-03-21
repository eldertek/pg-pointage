from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum, Count, Q

from ...models import StatistiquesTemps
from ...serializers import StatistiquesTempsSerializer
from .base import BaseModelViewSet
import logging

logger = logging.getLogger(__name__)

class StatistiquesViewSet(BaseModelViewSet):
    """
    API endpoint for accessing time statistics.
    """
    queryset = StatistiquesTemps.objects.all().order_by('-annee', '-mois')
    serializer_class = StatistiquesTempsSerializer
    
    def get_queryset(self):
        """
        Filter statistics based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        elif not self.request.user.is_superuser and self.request.user.role != 'manager':
            # Regular users only see their own statistics
            queryset = queryset.filter(user=self.request.user)
            
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
            
        # Filter by month/year
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        
        if month:
            queryset = queryset.filter(mois=int(month))
        if year:
            queryset = queryset.filter(annee=int(year))
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """
        Return statistics for the authenticated user
        """
        # Default to current month if not specified
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        queryset = self.get_queryset().filter(
            user=request.user,
            mois=month,
            annee=year
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Return summary statistics for all users in the user's organization
        """
        # Only managers and superusers can access summary statistics
        if not request.user.is_superuser and request.user.role != 'manager':
            return Response(
                {"detail": "You don't have permission to access summary statistics"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Default to current month if not specified
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        # Get all statistics for the specified month/year in the user's organization
        queryset = self.get_queryset().filter(mois=month, annee=year)
        
        # Calculate aggregates
        aggregates = queryset.aggregate(
            total_minutes_travaillees=Sum('minutes_travaillees'),
            total_minutes_retard=Sum('minutes_retard'),
            total_minutes_depart_anticipe=Sum('minutes_depart_anticipe'),
            total_minutes_absence=Sum('minutes_absence'),
            total_jours_travailles=Sum('jours_travailles'),
            count=Count('id')
        )
        
        # Convert to hours for better readability
        hours_worked = round(aggregates['total_minutes_travaillees'] / 60, 2) if aggregates['total_minutes_travaillees'] else 0
        hours_late = round(aggregates['total_minutes_retard'] / 60, 2) if aggregates['total_minutes_retard'] else 0
        hours_early = round(aggregates['total_minutes_depart_anticipe'] / 60, 2) if aggregates['total_minutes_depart_anticipe'] else 0
        hours_absent = round(aggregates['total_minutes_absence'] / 60, 2) if aggregates['total_minutes_absence'] else 0
        
        # Extract site statistics if a site is specified
        site_id = request.query_params.get('site', None)
        site_stats = None
        if site_id:
            site_queryset = queryset.filter(site_id=site_id)
            site_aggregates = site_queryset.aggregate(
                total_minutes_travaillees=Sum('minutes_travaillees'),
                total_minutes_retard=Sum('minutes_retard'),
                total_minutes_depart_anticipe=Sum('minutes_depart_anticipe'),
                total_minutes_absence=Sum('minutes_absence'),
                total_jours_travailles=Sum('jours_travailles'),
                count=Count('id')
            )
            
            site_stats = {
                'hours_worked': round(site_aggregates['total_minutes_travaillees'] / 60, 2) if site_aggregates['total_minutes_travaillees'] else 0,
                'hours_late': round(site_aggregates['total_minutes_retard'] / 60, 2) if site_aggregates['total_minutes_retard'] else 0,
                'hours_early': round(site_aggregates['total_minutes_depart_anticipe'] / 60, 2) if site_aggregates['total_minutes_depart_anticipe'] else 0,
                'hours_absent': round(site_aggregates['total_minutes_absence'] / 60, 2) if site_aggregates['total_minutes_absence'] else 0,
                'days_worked': site_aggregates['total_jours_travailles'] or 0,
                'user_count': site_aggregates['count'] or 0
            }
        
        # Build the response
        response_data = {
            'period': f"{month}/{year}",
            'hours_worked': hours_worked,
            'hours_late': hours_late,
            'hours_early': hours_early,
            'hours_absent': hours_absent,
            'days_worked': aggregates['total_jours_travailles'] or 0,
            'user_count': aggregates['count'] or 0
        }
        
        if site_stats:
            response_data['site_stats'] = site_stats
            
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """
        Recalculate statistics for a user and site
        """
        # Only managers and superusers can recalculate statistics
        if not request.user.is_superuser and request.user.role != 'manager':
            return Response(
                {"detail": "You don't have permission to recalculate statistics"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get required parameters
        user_id = request.data.get('user_id', None)
        site_id = request.data.get('site_id', None)
        
        if not user_id or not site_id:
            return Response(
                {"detail": "user_id and site_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Recalculate statistics from anomalies
            stats = StatistiquesTemps.update_from_anomalies(
                user_id=user_id,
                site_id=site_id
            )
            
            # Recalculate statistics from pointages
            stats = StatistiquesTemps.update_from_pointages(
                user_id=user_id,
                site_id=site_id
            )
            
            if stats:
                serializer = self.get_serializer(stats)
                return Response(serializer.data)
            else:
                return Response(
                    {"detail": "Statistics could not be recalculated"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error recalculating statistics: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 