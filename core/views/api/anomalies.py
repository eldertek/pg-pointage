from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q

from ...models import Anomalie
from ...serializers import AnomalieSerializer
from .base import BaseModelViewSet
import logging

logger = logging.getLogger(__name__)

class AnomalieViewSet(BaseModelViewSet):
    """
    API endpoint for managing anomalies.
    """
    queryset = Anomalie.objects.all().order_by('-date_creation')
    serializer_class = AnomalieSerializer
    search_fields = ['motif', 'user__username', 'site__name']
    
    def get_queryset(self):
        """
        Filter anomalies based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        elif not self.request.user.is_superuser and self.request.user.role != 'manager':
            # Regular users only see their own anomalies
            queryset = queryset.filter(user=self.request.user)
            
        # Filter by site
        site_id = self.request.query_params.get('site', None)
        if site_id:
            queryset = queryset.filter(site_id=site_id)
            
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by type
        type_param = self.request.query_params.get('type', None)
        if type_param:
            queryset = queryset.filter(type_anomalie=type_param)
            
        # Filter by date range
        date_from = self.request.query_params.get('from', None)
        date_to = self.request.query_params.get('to', None)
        
        if date_from:
            queryset = queryset.filter(date_creation__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_creation__lte=date_to)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def unprocessed(self, request):
        """
        Return all unprocessed anomalies
        """
        queryset = self.get_queryset().filter(status='en_attente')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_anomalies(self, request):
        """
        Return all anomalies for the authenticated user
        """
        queryset = self.get_queryset().filter(user=request.user)
        
        # Default to the last 30 days
        days = int(request.query_params.get('days', 30))
        if days > 0:
            from datetime import timedelta
            start_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(date_creation__gte=start_date)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process an anomaly (justify or reject)
        """
        anomalie = self.get_object()
        
        # Check if the user has permission to process this anomaly
        if not request.user.is_superuser and request.user.role != 'manager':
            return Response(
                {"detail": "You don't have permission to process anomalies"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get the new status and comment
        new_status = request.data.get('status', None)
        if not new_status or new_status not in ['justifiee', 'non_justifiee']:
            return Response(
                {"detail": "Status must be 'justifiee' or 'non_justifiee'"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        commentaire = request.data.get('commentaire', '')
        
        # Update the anomaly
        anomalie.status = new_status
        anomalie.commentaire_traitement = commentaire
        anomalie.date_traitement = timezone.now()
        anomalie.traite_par = request.user
        anomalie.save()
        
        serializer = self.get_serializer(anomalie)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def declare(self, request):
        """
        Declare a new anomaly
        """
        # Get required fields
        site_id = request.data.get('site_id', None)
        motif = request.data.get('motif', None)
        type_anomalie = request.data.get('type_anomalie', 'autre')
        
        if not site_id or not motif:
            return Response(
                {"detail": "site_id and motif are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create the anomaly
        try:
            from ...models import Site
            site = Site.objects.get(id=site_id)
            
            anomalie = Anomalie.objects.create(
                user=request.user,
                site=site,
                motif=motif,
                type_anomalie=type_anomalie,
                status='en_attente',
                organisation=request.user.organisation
            )
            
            serializer = self.get_serializer(anomalie)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Site.DoesNotExist:
            return Response(
                {"detail": "Site not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating anomaly: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 