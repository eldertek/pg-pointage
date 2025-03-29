from rest_framework import permissions

class HasOrganizationPermission(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier les droits d'accès aux organisations.
    """
    
    def has_permission(self, request, view):
        # Autoriser les super admins
        if request.user.is_super_admin:
            return True
            
        # Pour les autres rôles, vérifier l'accès à l'organisation
        organization_id = view.kwargs.get('organization_id') or request.data.get('organization')
        if not organization_id:
            return False
            
        return request.user.has_organization_permission(organization_id)
    
    def has_object_permission(self, request, view, obj):
        # Autoriser les super admins
        if request.user.is_super_admin:
            return True
            
        # Pour les autres objets, vérifier l'organisation
        organization = getattr(obj, 'organization', None)
        if not organization:
            return False
            
        return request.user.has_organization_permission(organization)

class IsSiteOrganizationManager(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement aux managers d'une organisation 
    de gérer ses sites et leurs ressources associées.
    """
    
    def has_permission(self, request, view):
        # Autoriser les requêtes en lecture (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Vérifier si l'utilisateur est un manager ou un admin
        return (
            request.user.is_authenticated and 
            (request.user.is_manager or request.user.is_admin or request.user.is_super_admin)
        )
    
    def has_object_permission(self, request, view, obj):
        # Autoriser les requêtes en lecture (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Les managers et admins peuvent gérer les sites de leur propre organisation
        site = obj
        if hasattr(obj, 'site'):  # Pour les objets liés à un site (Schedule, SiteEmployee, etc.)
            site = obj.site
            
        if request.user.is_super_admin:
            return True
            
        return (
            request.user.is_authenticated and 
            (request.user.is_manager or request.user.is_admin) and 
            request.user.has_organization_permission(site.organization)
        )

