from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import models

from ...models import Planning
from ...serializers import PlanningSerializer
from .base import BaseModelViewSet
import logging

logger = logging.getLogger(__name__)

class PlanningViewSet(BaseModelViewSet):
    """
    API endpoint for managing plannings.
    """
    queryset = Planning.objects.all().order_by('-actif', 'site__name')
    serializer_class = PlanningSerializer
    search_fields = ['site__name', 'user__username']
    
    def get_queryset(self):
        """
        Filter plannings based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
            
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by type
        planning_type = self.request.query_params.get('type', None)
        if planning_type:
            queryset = queryset.filter(type=planning_type)
            
        # Filter by active status
        active = self.request.query_params.get('active', None)
        if active is not None:
            is_active = active.lower() == 'true'
            queryset = queryset.filter(actif=is_active)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def user_plannings(self, request):
        """
        Return all plannings for the authenticated user
        """
        queryset = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Return all active plannings
        """
        queryset = self.get_queryset().filter(actif=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a planning
        """
        planning = self.get_object()
        planning.actif = not planning.actif
        planning.save()
        serializer = self.get_serializer(planning)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """
        Return all plannings active on a specific date
        """
        date_str = request.query_params.get('date', None)
        
        if not date_str:
            return Response(
                {"detail": "Date parameter is required (format: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get all plannings that are active on the specified date
        queryset = self.get_queryset().filter(actif=True)
        queryset = queryset.filter(
            # Date is within the start/end date range (if specified)
            (
                (models.Q(date_debut__isnull=True) | models.Q(date_debut__lte=date)) &
                (models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=date))
            )
        )
        
        # Get the day of the week and filter by that day
        day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
        day_fields = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        day_filter = {day_fields[day_of_week]: True}
        queryset = queryset.filter(**day_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 