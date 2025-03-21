from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q

from ...models import Pointage, Site, Planning
from ...serializers import PointageSerializer
from .base import BaseModelViewSet
import logging

logger = logging.getLogger(__name__)

class PointageViewSet(BaseModelViewSet):
    """
    API endpoint for managing pointages (time tracking).
    """
    queryset = Pointage.objects.all().order_by('-date_scan')
    serializer_class = PointageSerializer
    
    def get_queryset(self):
        """
        Filter pointages based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        elif not self.request.user.is_superuser and self.request.user.role != 'manager':
            # Regular users only see their own pointages
            queryset = queryset.filter(user=self.request.user)
            
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
            
        # Filter by date range
        date_from = self.request.query_params.get('from', None)
        date_to = self.request.query_params.get('to', None)
        
        if date_from:
            queryset = queryset.filter(date_scan__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_scan__lte=date_to)
            
        # Filter by type
        type_pointage = self.request.query_params.get('type', None)
        if type_pointage:
            queryset = queryset.filter(type_pointage=type_pointage)
            
        # Filter by periode
        periode = self.request.query_params.get('periode', None)
        if periode:
            queryset = queryset.filter(periode=periode)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Return all pointages for today
        """
        today = timezone.localtime().date()
        queryset = self.get_queryset().filter(
            date_scan__date=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_pointages(self, request):
        """
        Return all pointages for the authenticated user
        """
        queryset = self.get_queryset().filter(user=request.user)
        
        # Limit to the last 30 days by default
        days = int(request.query_params.get('days', 30))
        if days > 0:
            from datetime import timedelta
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(date_scan__gte=start_date)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def scan_qr(self, request):
        """
        Create a new pointage from a QR code scan
        """
        qr_value = request.data.get('qr_value', None)
        if not qr_value:
            return Response(
                {"detail": "QR code value is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Find the site with this QR code
        try:
            site = Site.objects.get(qr_code_value=qr_value)
        except Site.DoesNotExist:
            return Response(
                {"detail": "Invalid QR code"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Get the type of pointage (default to ENTREE if not specified)
        type_pointage = request.data.get('type_pointage', 'ENTREE')
        if type_pointage not in ['ENTREE', 'SORTIE']:
            return Response(
                {"detail": "Invalid pointage type. Must be ENTREE or SORTIE"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create the pointage
        now = timezone.now()
        pointage = Pointage.objects.create(
            user=request.user,
            site=site,
            date_scan=now,
            type_pointage=type_pointage,
            organisation=request.user.organisation
        )
        
        # Find the associated planning and update the periode
        pointage.trouver_planning_associe()
        
        # Save the pointage to trigger calculations in the save method
        pointage.save()
        
        # Create anomalies if needed
        pointage.creer_anomalie_si_necessaire()
        
        serializer = self.get_serializer(pointage)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def with_anomalies(self, request):
        """
        Return all pointages with retards or départs anticipés
        """
        queryset = self.get_queryset().filter(
            Q(retard__gt=0) | Q(depart_anticip__gt=0)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 