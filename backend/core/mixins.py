from rest_framework import serializers
from django.core.exceptions import PermissionDenied

class OrganizationPermissionMixin:
    """Mixin pour gérer les permissions liées aux organisations"""
    
    def has_organization_permission(self, organization_id):
        user = self.context['request'].user
        if user.is_super_admin:
            return True
        return user.organizations.filter(id=organization_id).exists()

    def validate_organization(self, organization_id):
        if not self.has_organization_permission(organization_id):
            raise serializers.ValidationError({
                "organization": "Vous n'avez pas accès à cette organisation"
            })

class RolePermissionMixin:
    """Mixin pour gérer les permissions liées aux rôles"""
    
    def validate_role_permission(self, required_roles):
        user = self.context['request'].user
        if user.role not in required_roles and not user.is_super_admin:
            raise PermissionDenied("Vous n'avez pas les permissions nécessaires pour effectuer cette action")

class SitePermissionMixin:
    """Mixin pour gérer les permissions liées aux sites"""
    
    def has_site_permission(self, site):
        user = self.context['request'].user
        if user.is_super_admin:
            return True
        return user.organizations.filter(sites=site).exists()

    def validate_site(self, site):
        if not self.has_site_permission(site):
            raise serializers.ValidationError({
                "site": "Vous n'avez pas accès à ce site"
            }) 