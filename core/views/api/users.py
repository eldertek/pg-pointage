from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import Group
from django.db.models import Q

from ...models import User
from ...serializers import UserSerializer, GroupSerializer
from .base import BaseModelViewSet
import logging

logger = logging.getLogger(__name__)

class UserViewSet(BaseModelViewSet):
    """
    API endpoint for managing users.
    """
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self):
        """
        Filter users based on the requesting user's role and organization
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin can see all users
        if user.is_superuser:
            return queryset
            
        # Managers can see users in their organization
        if user.role == 'manager' and user.organisation:
            return queryset.filter(organisation=user.organisation)
            
        # Regular users can only see themselves
        return queryset.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the currently authenticated user
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def gardiens(self, request):
        """
        Return all users with the role 'gardien' in the user's organization
        """
        queryset = self.get_queryset().filter(role='gardien')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def agents_nettoyage(self, request):
        """
        Return all users with the role 'agent_de_nettoyage' in the user's organization
        """
        queryset = self.get_queryset().filter(role='agent_de_nettoyage')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def managers(self, request):
        """
        Return all users with the role 'manager' in the user's organization
        """
        queryset = self.get_queryset().filter(role='manager')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GroupViewSet(BaseModelViewSet):
    """
    API endpoint for managing organizations (groups).
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    search_fields = ['name']
    
    def get_permissions(self):
        """
        Only superadmins can manage organizations
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Filter organizations based on user's role
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Super admin can see all organizations
        if user.is_superuser:
            return queryset
            
        # Other users can only see their own organization
        if user.organisation:
            return queryset.filter(id=user.organisation.id)
            
        return Group.objects.none() 