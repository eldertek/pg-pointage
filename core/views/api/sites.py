from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from ...models import Site
from ...serializers import SiteSerializer
from .base import BaseModelViewSet
import logging

logger = logging.getLogger(__name__)

class SiteViewSet(BaseModelViewSet):
    """
    API endpoint for managing sites.
    """
    queryset = Site.objects.all().order_by('name')
    serializer_class = SiteSerializer
    search_fields = ['name', 'adresse', 'qr_code_value']
    
    @action(detail=True, methods=['get'])
    def plannings(self, request, pk=None):
        """
        Return all plannings for a site
        """
        site = self.get_object()
        from ...models import Planning
        from ...serializers import PlanningSerializer
        
        plannings = Planning.objects.filter(site=site)
        if not request.user.is_superuser and request.user.organisation:
            plannings = plannings.filter(organisation=request.user.organisation)
            
        serializer = PlanningSerializer(plannings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pointages(self, request, pk=None):
        """
        Return all pointages for a site
        """
        site = self.get_object()
        from ...models import Pointage
        from ...serializers import PointageSerializer
        
        # Get optional date range filters
        date_from = request.query_params.get('from', None)
        date_to = request.query_params.get('to', None)
        
        pointages = Pointage.objects.filter(site=site)
        
        # Apply date filters if provided
        if date_from:
            pointages = pointages.filter(date_scan__gte=date_from)
        if date_to:
            pointages = pointages.filter(date_scan__lte=date_to)
            
        # Apply organization filter for non-superusers
        if not request.user.is_superuser and request.user.organisation:
            pointages = pointages.filter(organisation=request.user.organisation)
            
        serializer = PointageSerializer(pointages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def anomalies(self, request, pk=None):
        """
        Return all anomalies for a site
        """
        site = self.get_object()
        from ...models import Anomalie
        from ...serializers import AnomalieSerializer
        
        # Get optional status filter
        status_filter = request.query_params.get('status', None)
        
        anomalies = Anomalie.objects.filter(site=site)
        
        # Apply status filter if provided
        if status_filter:
            anomalies = anomalies.filter(status=status_filter)
            
        # Apply organization filter for non-superusers
        if not request.user.is_superuser and request.user.organisation:
            anomalies = anomalies.filter(organisation=request.user.organisation)
            
        serializer = AnomalieSerializer(anomalies, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def verify_qr(self, request, pk=None):
        """
        Verify if a QR code value is valid for this site
        """
        site = self.get_object()
        qr_value = request.query_params.get('qr_value', None)
        
        if not qr_value:
            return Response(
                {"detail": "QR code value is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if site.qr_code_value == qr_value:
            return Response({"valid": True, "site_id": site.id, "site_name": site.name})
        else:
            return Response({"valid": False}, status=status.HTTP_404_NOT_FOUND) 