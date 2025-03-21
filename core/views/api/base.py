from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all API endpoints.
    Implements common functionality like filtering by organization.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter queryset based on user's organization and any additional filters
        """
        queryset = super().get_queryset()
        
        # Apply organization filter for non-superusers
        if not self.request.user.is_superuser and hasattr(queryset.model, 'organisation'):
            queryset = queryset.filter(
                Q(organisation=self.request.user.organisation) | 
                Q(organisation__isnull=True)
            )
            
        # Apply any search filters
        search = self.request.query_params.get('search', None)
        if search and hasattr(self, 'search_fields') and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(q_objects)
            
        return queryset
    
    def perform_create(self, serializer):
        """
        When creating a new object, set the organization to the user's organization
        """
        if hasattr(serializer.Meta.model, 'organisation') and self.request.user.organisation:
            serializer.save(organisation=self.request.user.organisation)
        else:
            serializer.save()
            
    def handle_exception(self, exc):
        """
        Log exceptions and provide better error responses
        """
        logger.error(f"API error in {self.__class__.__name__}: {str(exc)}")
        return super().handle_exception(exc) 