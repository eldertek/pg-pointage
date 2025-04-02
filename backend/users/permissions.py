"""Permissions pour les utilisateurs"""

from rest_framework import permissions
from .models import User


class HasUserPermission(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier les droits d'accès aux utilisateurs.
    """

    def has_permission(self, request, view):
        # Autoriser les super admins
        if request.user.is_super_admin:
            return True

        # Pour les autres rôles, vérifier l'accès selon la hiérarchie
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Seuls les super admin et admin peuvent créer/supprimer des utilisateurs
        if request.method == 'POST' or request.method == 'DELETE':
            return request.user.is_super_admin or request.user.is_admin

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Super admin peut tout faire
        if user.is_super_admin:
            return True

        # Un utilisateur peut toujours accéder à son propre profil
        if obj.id == user.id:
            return True

        # Admin peut accéder aux utilisateurs de ses organisations
        if user.is_admin:
            return obj.organizations.filter(id__in=user.organizations.values_list('id', flat=True)).exists()

        # Manager peut accéder aux employés de ses organisations
        if user.is_manager:
            return (
                obj.role == User.Role.EMPLOYEE and
                obj.organizations.filter(id__in=user.organizations.values_list('id', flat=True)).exists()
            )

        # Employé ne peut accéder qu'à son propre profil
        return obj.id == user.id 