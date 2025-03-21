from rest_framework import permissions

class IsSiteOrganizationManager(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement aux managers d'une organisation 
    de gérer ses sites et leurs ressources associées.
    """
    
    def has_permission(self, request, view):
        # Autoriser les requêtes en lecture (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Vérifier si l'utilisateur est un manager avec une organisation
        return request.user.is_authenticated and request.user.is_manager and request.user.organization is not None
    
    def has_object_permission(self, request, view, obj):
        # Autoriser les requêtes en lecture (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Les managers peuvent gérer les sites de leur propre organisation
        site = obj
        if hasattr(obj, 'site'):  # Pour les objets liés à un site (Schedule, SiteEmployee, etc.)
            site = obj.site
            
        return request.user.is_authenticated and request.user.is_manager and request.user.organization == site.organization

