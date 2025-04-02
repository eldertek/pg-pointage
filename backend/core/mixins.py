"""Mixins pour la gestion des permissions (organisations, rôles et sites)."""

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from users.models import User


class OrganizationPermissionMixin:
    """Mixin pour gérer les permissions liées aux organisations."""

    def has_organization_permission(self, organization_id):
        """Vérifie si l'utilisateur a accès à l'organisation donnée.

        Args:
            organization_id: L'ID de l'organisation à vérifier.

        Returns:
            bool: True si l'utilisateur a accès, False sinon.
        """
        user = self.context['request'].user
        if user.is_super_admin:
            return True
        return user.organizations.filter(id=organization_id).exists()

    def validate_organization(self, organization_id):
        """Valide l'accès à l'organisation.

        Args:
            organization_id: L'ID de l'organisation à valider.

        Raises:
            ValidationError: Si l'utilisateur n'a pas accès à l'organisation.
        """
        if not self.has_organization_permission(organization_id):
            raise serializers.ValidationError({
                "organization": "Vous n'avez pas accès à cette organisation"
            })

    def has_user_permission(self, target_user):
        """Vérifie si l'utilisateur a accès à l'utilisateur cible.

        Args:
            target_user: L'utilisateur cible à vérifier.

        Returns:
            bool: True si l'utilisateur a accès, False sinon.
        """
        user = self.context['request'].user

        # Super admin peut accéder à tous les utilisateurs
        if user.is_super_admin:
            return True

        # Un utilisateur peut toujours accéder à son propre profil
        if user.id == target_user.id:
            return True

        # Vérifier si l'utilisateur et la cible sont dans la même organisation
        user_orgs = set(user.organizations.values_list('id', flat=True))
        target_orgs = set(target_user.organizations.values_list('id', flat=True))
        common_orgs = user_orgs & target_orgs

        if not common_orgs:
            return False

        # Admin peut accéder à tous les utilisateurs de son organisation
        if user.is_admin:
            return True

        # Manager peut accéder aux employés de son organisation
        if user.is_manager:
            return target_user.is_employee

        # Employé ne peut accéder qu'à son propre profil (déjà vérifié plus haut)
        return False


class RolePermissionMixin:
    """Mixin pour gérer les permissions liées aux rôles."""
    ROLE_HIERARCHY = {
        User.Role.SUPER_ADMIN: [
            User.Role.SUPER_ADMIN,
            User.Role.ADMIN,
            User.Role.MANAGER,
            User.Role.EMPLOYEE
        ],
        User.Role.ADMIN: [User.Role.ADMIN, User.Role.MANAGER, User.Role.EMPLOYEE],
        User.Role.MANAGER: [User.Role.MANAGER, User.Role.EMPLOYEE],
        User.Role.EMPLOYEE: [User.Role.EMPLOYEE]
    }

    def validate_role_permission(self, required_roles):
        """Valide les permissions basées sur les rôles requis.

        Args:
            required_roles: Liste des rôles requis ou un seul rôle.

        Returns:
            bool: True si l'utilisateur a les permissions nécessaires.

        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les permissions requises.
        """
        user = self.context['request'].user
        if user.is_super_admin:
            return True
        if not isinstance(required_roles, (list, tuple)):
            required_roles = [required_roles]
        allowed_roles = self.ROLE_HIERARCHY.get(user.role, [])
        if not any(role in allowed_roles for role in required_roles):
            raise PermissionDenied(
                "Vous n'avez pas les permissions nécessaires pour cette action"
            )
        return True


class SitePermissionMixin:
    """Mixin pour gérer les permissions liées aux sites."""

    def has_site_permission(self, site):
        """Vérifie si l'utilisateur a accès au site donné.

        Args:
            site: L'instance du site à vérifier.

        Returns:
            bool: True si l'utilisateur a accès, False sinon.
        """
        user = self.context['request'].user
        if user.is_super_admin:
            return True
        if site is None:
            return False
        return user.organizations.filter(id=site.organization.id).exists()

    def validate_site(self, site):
        """Valide l'accès au site.

        Args:
            site: L'instance du site à valider.

        Raises:
            ValidationError: Si l'utilisateur n'a pas accès au site ou si le site n'existe pas.
        """
        if site is None:
            raise serializers.ValidationError({
                'site': "Le site spécifié n'existe pas"
            })
        if not self.has_site_permission(site):
            raise serializers.ValidationError({
                'site': "Vous n'avez pas accès à ce site"
            })
