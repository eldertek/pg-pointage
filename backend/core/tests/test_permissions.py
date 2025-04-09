"""Tests pour les permissions"""
import pytest

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework import serializers
from rest_framework.test import APIClient
from users.models import User
from organizations.models import Organization
from sites.models import Site, SiteEmployee
from core.mixins import OrganizationPermissionMixin, RolePermissionMixin, SitePermissionMixin

@pytest.fixture
def create_user():
    """Fixture pour créer un utilisateur avec un rôle spécifique."""
    def _create_user(role, **kwargs):
        user_data = {
            'username': f'test_{role.lower()}',
            'email': f'{role.lower()}@test.com',
            'password': 'testpass123',
            'role': role,
            **kwargs
        }
        return User.objects.create_user(**user_data)
    return _create_user


@pytest.fixture
def create_organization():
    """Fixture pour créer une organisation."""
    def _create_organization(**kwargs):
        org_data = {
            'name': 'Test Organization',
            'org_id': 'O001',
            **kwargs
        }
        return Organization.objects.create(**org_data)
    return _create_organization


@pytest.fixture
def create_site():
    """Fixture pour créer un site."""
    def _create_site(organization, **kwargs):
        site_data = {
            'name': 'Test Site',
            'address': '123 Test St',
            'postal_code': '75000',
            'city': 'Paris',
            'organization': organization,
            'nfc_id': f'{organization.org_id}-S0001',
            **kwargs
        }
        return Site.objects.create(**site_data)
    return _create_site


class TestOrganizationPermissions(TestCase):
    """Tests des permissions au niveau de l'organisation."""
    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin',
            email='super@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )

        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Associer les utilisateurs aux organisations
        self.admin.organizations.add(self.org1)
        self.manager.organizations.add(self.org1)
        self.employee.organizations.add(self.org1)

    def test_super_admin_has_all_organization_permissions(self):
        """Le super admin doit avoir accès à toutes les organisations"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}

        self.assertTrue(mixin.has_organization_permission(self.org1.id))
        self.assertTrue(mixin.has_organization_permission(self.org2.id))

    def test_admin_has_limited_organization_permissions(self):
        """L'admin ne doit avoir accès qu'à ses organisations"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type('Request', (), {'user': self.admin})}

        self.assertTrue(mixin.has_organization_permission(self.org1.id))
        self.assertFalse(mixin.has_organization_permission(self.org2.id))

    def test_manager_has_limited_organization_permissions(self):
        """Le manager ne doit avoir accès qu'à ses organisations"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}

        self.assertTrue(mixin.has_organization_permission(self.org1.id))
        self.assertFalse(mixin.has_organization_permission(self.org2.id))

    def test_employee_has_limited_organization_permissions(self):
        """L'employé ne doit avoir accès qu'à ses organisations"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}

        self.assertTrue(mixin.has_organization_permission(self.org1.id))
        self.assertFalse(mixin.has_organization_permission(self.org2.id))


class TestRolePermissions(TestCase):
    """Tests des permissions basées sur les rôles."""
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='super_admin',
            email='super@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )

    def test_super_admin_has_all_role_permissions(self):
        """Le super admin doit avoir toutes les permissions de rôle"""
        mixin = RolePermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}

        # Test avec différentes combinaisons de rôles requis
        mixin.validate_role_permission([User.Role.SUPER_ADMIN])
        mixin.validate_role_permission([User.Role.ADMIN])
        mixin.validate_role_permission([User.Role.MANAGER])
        mixin.validate_role_permission([User.Role.EMPLOYEE])

    def test_admin_role_permissions(self):
        """L'admin doit avoir les permissions appropriées"""
        mixin = RolePermissionMixin()
        mixin.context = {'request': type('Request', (), {'user': self.admin})}

        # L'admin peut accéder aux permissions ADMIN et inférieures
        mixin.validate_role_permission([User.Role.ADMIN])
        mixin.validate_role_permission([User.Role.MANAGER])
        mixin.validate_role_permission([User.Role.EMPLOYEE])

        # L'admin ne peut pas accéder aux permissions SUPER_ADMIN
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.SUPER_ADMIN])

    def test_manager_role_permissions(self):
        """Le manager doit avoir les permissions appropriées"""
        mixin = RolePermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}

        # Le manager peut accéder aux permissions MANAGER et inférieures
        mixin.validate_role_permission([User.Role.MANAGER])
        mixin.validate_role_permission([User.Role.EMPLOYEE])

        # Le manager ne peut pas accéder aux permissions supérieures
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.SUPER_ADMIN])
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.ADMIN])

    def test_employee_role_permissions(self):
        """L'employé doit avoir les permissions appropriées"""
        mixin = RolePermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}

        # L'employé peut accéder uniquement aux permissions EMPLOYEE
        mixin.validate_role_permission([User.Role.EMPLOYEE])

        # L'employé ne peut pas accéder aux permissions supérieures
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.SUPER_ADMIN])
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.ADMIN])
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.MANAGER])


class TestSitePermissions(TestCase):
    """Tests des permissions au niveau des sites."""
    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin',
            email='super@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )

        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Créer les sites
        self.site1 = Site.objects.create(
            name='Site 1',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.org1,
            nfc_id='O001-S0001'
        )
        self.site2 = Site.objects.create(
            name='Site 2',
            address='456 Test Ave',
            postal_code='75001',
            city='Paris',
            organization=self.org2,
            nfc_id='O002-S0001'
        )

        # Associer les utilisateurs aux organisations
        self.admin.organizations.add(self.org1)
        self.manager.organizations.add(self.org1)
        self.employee.organizations.add(self.org1)

        # Définir le manager du site
        self.site1.manager = self.manager
        self.site1.save()

        # Créer l'association site-employé
        SiteEmployee.objects.create(
            site=self.site1,
            employee=self.employee,
            is_active=True
        )

    def test_super_admin_has_all_site_permissions(self):
        """Le super admin doit avoir accès à tous les sites"""
        mixin = SitePermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}

        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertTrue(mixin.has_site_permission(self.site2))

    def test_admin_has_limited_site_permissions(self):
        """L'admin ne doit avoir accès qu'aux sites de ses organisations"""
        mixin = SitePermissionMixin()
        mixin.context = {'request': type('Request', (), {'user': self.admin})}

        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertFalse(mixin.has_site_permission(self.site2))

    def test_manager_has_limited_site_permissions(self):
        """Le manager ne doit avoir accès qu'aux sites de ses organisations"""
        mixin = SitePermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}

        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertFalse(mixin.has_site_permission(self.site2))

    def test_employee_has_limited_site_permissions(self):
        """L'employé ne doit avoir accès qu'aux sites de ses organisations"""
        mixin = SitePermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}

        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertFalse(mixin.has_site_permission(self.site2))

    def test_site_validation_raises_error_for_unauthorized_access(self):
        """La validation du site doit lever une erreur pour un accès non autorisé"""
        mixin = SitePermissionMixin()
        mixin.context = {'request': type('Request', (), {'user': self.admin})}

        # La validation doit réussir pour un site autorisé
        mixin.validate_site(self.site1)

        # La validation doit échouer pour un site non autorisé
        with self.assertRaises(serializers.ValidationError):
            mixin.validate_site(self.site2)


class TestCRUDPermissions(TestCase):
    """Tests des permissions CRUD pour différents rôles."""
    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin',
            email='super@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )

        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Associer les utilisateurs aux organisations
        self.admin.organizations.add(self.org1)
        self.manager.organizations.add(self.org1)
        self.employee.organizations.add(self.org1)

    def test_user_crud_permissions(self):
        """Test des permissions CRUD sur les utilisateurs"""
        mixin = RolePermissionMixin()

        # Super Admin peut tout faire
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}
        mixin.validate_role_permission(
            [User.Role.SUPER_ADMIN])  # Création/suppression
        mixin.validate_role_permission([User.Role.ADMIN])  # Modification
        mixin.validate_role_permission([User.Role.MANAGER])  # Consultation

        # Admin peut créer/supprimer/modifier/consulter
        mixin.context = {'request': type('Request', (), {'user': self.admin})}
        # Création/suppression/modification
        mixin.validate_role_permission([User.Role.ADMIN])
        mixin.validate_role_permission([User.Role.MANAGER])  # Consultation

        # Manager peut modifier/consulter
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}
        mixin.validate_role_permission(
            [User.Role.MANAGER])  # Modification/consultation
        with self.assertRaises(PermissionDenied):
            # Pas de création/suppression
            mixin.validate_role_permission([User.Role.ADMIN])

        # Employé ne peut que consulter son propre profil
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission(
                [User.Role.MANAGER])  # Pas de modification
        with self.assertRaises(PermissionDenied):
            # Pas de création/suppression
            mixin.validate_role_permission([User.Role.ADMIN])

    def test_site_crud_permissions(self):
        """Test des permissions CRUD sur les sites"""
        mixin = RolePermissionMixin()

        # Super Admin peut tout faire
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}
        mixin.validate_role_permission(
            [User.Role.SUPER_ADMIN])  # Création/suppression
        mixin.validate_role_permission([User.Role.ADMIN])  # Modification
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation

        # Admin peut créer/supprimer/modifier/consulter
        mixin.context = {'request': type('Request', (), {'user': self.admin})}
        # Création/suppression/modification
        mixin.validate_role_permission([User.Role.ADMIN])
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation

        # Manager peut modifier/consulter
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}
        mixin.validate_role_permission([User.Role.MANAGER])  # Modification
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation
        with self.assertRaises(PermissionDenied):
            # Pas de création/suppression
            mixin.validate_role_permission([User.Role.ADMIN])

        # Employé peut consulter
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission(
                [User.Role.MANAGER])  # Pas de modification
        with self.assertRaises(PermissionDenied):
            # Pas de création/suppression
            mixin.validate_role_permission([User.Role.ADMIN])

    def test_planning_crud_permissions(self):
        """Test des permissions CRUD sur les plannings"""
        mixin = RolePermissionMixin()

        # Super Admin peut tout faire
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}
        mixin.validate_role_permission(
            [User.Role.SUPER_ADMIN])  # Création/suppression
        mixin.validate_role_permission([User.Role.ADMIN])  # Modification
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation

        # Admin peut créer/supprimer/modifier/consulter
        mixin.context = {'request': type('Request', (), {'user': self.admin})}
        # Création/suppression/modification
        mixin.validate_role_permission([User.Role.ADMIN])
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation

        # Manager peut modifier/consulter
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}
        mixin.validate_role_permission([User.Role.MANAGER])  # Modification
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation
        with self.assertRaises(PermissionDenied):
            # Pas de création/suppression
            mixin.validate_role_permission([User.Role.ADMIN])

        # Employé peut consulter
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}
        mixin.validate_role_permission([User.Role.EMPLOYEE])  # Consultation
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission(
                [User.Role.MANAGER])  # Pas de modification
        with self.assertRaises(PermissionDenied):
            # Pas de création/suppression
            mixin.validate_role_permission([User.Role.ADMIN])

    def test_report_generation_permissions(self):
        """Test des permissions pour la génération de rapports"""
        mixin = RolePermissionMixin()

        # Super Admin peut générer des rapports
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}
        mixin.validate_role_permission([User.Role.SUPER_ADMIN])

        # Admin peut générer des rapports
        mixin.context = {'request': type('Request', (), {'user': self.admin})}
        mixin.validate_role_permission([User.Role.ADMIN])

        # Manager peut générer des rapports
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}
        mixin.validate_role_permission([User.Role.MANAGER])

        # Employé ne peut pas générer de rapports
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.MANAGER])

    def test_access_management_permissions(self):
        """Test des permissions pour la gestion des accès"""
        mixin = RolePermissionMixin()

        # Super Admin peut gérer les accès
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}
        mixin.validate_role_permission([User.Role.SUPER_ADMIN])

        # Admin ne peut pas gérer les accès
        mixin.context = {'request': type('Request', (), {'user': self.admin})}
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.SUPER_ADMIN])

        # Manager ne peut pas gérer les accès
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager})}
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.SUPER_ADMIN])

        # Employé ne peut pas gérer les accès
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee})}
        with self.assertRaises(PermissionDenied):
            mixin.validate_role_permission([User.Role.SUPER_ADMIN])

    def test_settings_permissions(self):
        """Test des permissions pour les paramètres"""
        mixin = RolePermissionMixin()

        # Tous les rôles peuvent consulter et modifier les paramètres
        for user in [self.super_admin, self.admin, self.manager, self.employee]:
            mixin.context = {'request': type('Request', (), {'user': user})}
            mixin.validate_role_permission(
                [User.Role.EMPLOYEE])  # Consultation/modification


class TestInformationVisibilityRestrictions(TestCase):
    """Tests des restrictions de visibilité des informations selon les rôles."""
    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin',
            email='super@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )
        self.admin1 = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.admin2 = User.objects.create_user(
            username='admin2',
            email='admin2@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.manager1 = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.manager2 = User.objects.create_user(
            username='manager2',
            email='manager2@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.employee1 = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee2 = User.objects.create_user(
            username='employee2',
            email='employee2@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )

        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Créer les sites
        self.site1 = Site.objects.create(
            name='Site 1',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.org1,
            nfc_id='O001-S0001'
        )
        self.site2 = Site.objects.create(
            name='Site 2',
            address='456 Test Ave',
            postal_code='75001',
            city='Paris',
            organization=self.org2,
            nfc_id='O002-S0001'
        )

        # Associer les utilisateurs aux organisations
        self.admin1.organizations.add(self.org1)
        self.admin2.organizations.add(self.org2)
        self.manager1.organizations.add(self.org1)
        self.manager2.organizations.add(self.org2)
        self.employee1.organizations.add(self.org1)
        self.employee2.organizations.add(self.org2)

        # Définir les managers des sites
        self.site1.manager = self.manager1
        self.site1.save()
        self.site2.manager = self.manager2
        self.site2.save()

    def test_admin_organization_visibility(self):
        """Test de la visibilité des informations pour les admins"""
        mixin = OrganizationPermissionMixin()

        # Admin1 ne doit voir que org1
        mixin.context = {'request': type('Request', (), {'user': self.admin1})}
        self.assertTrue(mixin.has_organization_permission(self.org1.id))
        self.assertFalse(mixin.has_organization_permission(self.org2.id))

        # Admin2 ne doit voir que org2
        mixin.context = {'request': type('Request', (), {'user': self.admin2})}
        self.assertFalse(mixin.has_organization_permission(self.org1.id))
        self.assertTrue(mixin.has_organization_permission(self.org2.id))

    def test_manager_user_visibility(self):
        """Test de la visibilité des utilisateurs pour les managers"""
        mixin = OrganizationPermissionMixin()

        # Manager1 ne doit voir que les utilisateurs de org1
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager1})}
        self.assertTrue(mixin.has_organization_permission(self.org1.id))
        self.assertFalse(mixin.has_organization_permission(self.org2.id))

        # Manager2 ne doit voir que les utilisateurs de org2
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager2})}
        self.assertFalse(mixin.has_organization_permission(self.org1.id))
        self.assertTrue(mixin.has_organization_permission(self.org2.id))

    def test_employee_site_visibility(self):
        """Test de la visibilité des sites pour les employés"""
        mixin = SitePermissionMixin()

        # Employee1 ne doit voir que les sites de org1
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee1})}
        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertFalse(mixin.has_site_permission(self.site2))

        # Employee2 ne doit voir que les sites de org2
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee2})}
        self.assertFalse(mixin.has_site_permission(self.site1))
        self.assertTrue(mixin.has_site_permission(self.site2))

    def test_super_admin_full_visibility(self):
        """Test de la visibilité complète pour le super admin"""
        org_mixin = OrganizationPermissionMixin()
        site_mixin = SitePermissionMixin()
        org_mixin.context = site_mixin.context = {
            'request': type('Request', (), {'user': self.super_admin})}

        # Le super admin doit voir toutes les organisations
        self.assertTrue(org_mixin.has_organization_permission(self.org1.id))
        self.assertTrue(org_mixin.has_organization_permission(self.org2.id))

        # Le super admin doit voir tous les sites
        self.assertTrue(site_mixin.has_site_permission(self.site1))
        self.assertTrue(site_mixin.has_site_permission(self.site2))

    def test_cross_organization_visibility(self):
        """Test des restrictions de visibilité entre organisations"""
        org_mixin = OrganizationPermissionMixin()
        site_mixin = SitePermissionMixin()

        # Admin1 ne doit pas voir les utilisateurs de org2
        org_mixin.context = {'request': type(
            'Request', (), {'user': self.admin1})}
        self.assertFalse(org_mixin.has_organization_permission(self.org2.id))

        # Manager1 ne doit pas voir les sites de org2
        site_mixin.context = {'request': type(
            'Request', (), {'user': self.manager1})}
        self.assertFalse(site_mixin.has_site_permission(self.site2))

        # Employee1 ne doit pas voir les informations de org2
        org_mixin.context = site_mixin.context = {
            'request': type('Request', (), {'user': self.employee1})}
        self.assertFalse(org_mixin.has_organization_permission(self.org2.id))
        self.assertFalse(site_mixin.has_site_permission(self.site2))


class TestUserHierarchyAccess(TestCase):
    """Tests de la hiérarchie d'accès des utilisateurs."""
    def setUp(self):
        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Créer les utilisateurs avec différents rôles dans org1
        self.super_admin = User.objects.create_user(
            username='super_admin',
            email='super@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )

        self.admin_org1 = User.objects.create_user(
            username='admin_org1',
            email='admin_org1@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.admin_org1.organizations.add(self.org1)

        self.admin_org2 = User.objects.create_user(
            username='admin_org2',
            email='admin_org2@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.admin_org2.organizations.add(self.org2)

        self.manager1_org1 = User.objects.create_user(
            username='manager1_org1',
            email='manager1_org1@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.manager1_org1.organizations.add(self.org1)

        self.manager2_org1 = User.objects.create_user(
            username='manager2_org1',
            email='manager2_org1@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.manager2_org1.organizations.add(self.org1)

        self.employee1_org1 = User.objects.create_user(
            username='employee1_org1',
            email='employee1_org1@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee1_org1.organizations.add(self.org1)

        self.employee2_org1 = User.objects.create_user(
            username='employee2_org1',
            email='employee2_org1@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee2_org1.organizations.add(self.org1)

        self.employee_org2 = User.objects.create_user(
            username='employee_org2',
            email='employee_org2@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee_org2.organizations.add(self.org2)

    def test_admin_can_access_all_users_in_organization(self):
        """Un admin doit pouvoir accéder à tous les utilisateurs de son organisation"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.admin_org1})}

        # L'admin de org1 doit pouvoir accéder aux utilisateurs de org1
        self.assertTrue(mixin.has_user_permission(self.manager1_org1))
        self.assertTrue(mixin.has_user_permission(self.manager2_org1))
        self.assertTrue(mixin.has_user_permission(self.employee1_org1))
        self.assertTrue(mixin.has_user_permission(self.employee2_org1))

        # L'admin de org1 ne doit pas pouvoir accéder aux utilisateurs de org2
        self.assertFalse(mixin.has_user_permission(self.admin_org2))
        self.assertFalse(mixin.has_user_permission(self.employee_org2))

    def test_manager_can_access_employees_in_organization(self):
        """Un manager doit pouvoir accéder aux employés de son organisation"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager1_org1})}

        # Le manager doit pouvoir accéder aux employés de son organisation
        self.assertTrue(mixin.has_user_permission(self.employee1_org1))
        self.assertTrue(mixin.has_user_permission(self.employee2_org1))

        # Le manager ne doit pas pouvoir accéder aux autres managers ou admins
        self.assertFalse(mixin.has_user_permission(self.admin_org1))
        self.assertFalse(mixin.has_user_permission(self.manager2_org1))

        # Le manager ne doit pas pouvoir accéder aux utilisateurs d'autres organisations
        self.assertFalse(mixin.has_user_permission(self.employee_org2))

    def test_employee_can_only_access_own_profile(self):
        """Un employé ne doit pouvoir accéder qu'à son propre profil"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee1_org1})}

        # L'employé doit pouvoir accéder à son propre profil
        self.assertTrue(mixin.has_user_permission(self.employee1_org1))

        # L'employé ne doit pas pouvoir accéder aux autres profils
        self.assertFalse(mixin.has_user_permission(self.employee2_org1))
        self.assertFalse(mixin.has_user_permission(self.manager1_org1))
        self.assertFalse(mixin.has_user_permission(self.admin_org1))

    def test_super_admin_can_access_all_users(self):
        """Un super admin doit pouvoir accéder à tous les utilisateurs"""
        mixin = OrganizationPermissionMixin()
        mixin.context = {'request': type(
            'Request', (), {'user': self.super_admin})}

        # Le super admin doit pouvoir accéder à tous les utilisateurs
        self.assertTrue(mixin.has_user_permission(self.admin_org1))
        self.assertTrue(mixin.has_user_permission(self.admin_org2))
        self.assertTrue(mixin.has_user_permission(self.manager1_org1))
        self.assertTrue(mixin.has_user_permission(self.manager2_org1))
        self.assertTrue(mixin.has_user_permission(self.employee1_org1))
        self.assertTrue(mixin.has_user_permission(self.employee2_org1))
        self.assertTrue(mixin.has_user_permission(self.employee_org2))

    def test_cross_organization_access_denied(self):
        """Vérification de l'accès inter-organisations"""
        mixin = OrganizationPermissionMixin()

        # Admin de org2 essayant d'accéder aux utilisateurs de org1
        mixin.context = {'request': type(
            'Request', (), {'user': self.admin_org2})}
        self.assertFalse(mixin.has_user_permission(self.employee1_org1))
        self.assertFalse(mixin.has_user_permission(self.manager1_org1))

        # Manager de org1 essayant d'accéder aux utilisateurs de org2
        mixin.context = {'request': type(
            'Request', (), {'user': self.manager1_org1})}
        self.assertFalse(mixin.has_user_permission(self.employee_org2))

        # Employé de org1 essayant d'accéder aux utilisateurs de org2
        mixin.context = {'request': type(
            'Request', (), {'user': self.employee1_org1})}
        self.assertFalse(mixin.has_user_permission(self.employee_org2))


class TestUserAPIPermissions(TestCase):
    """Tests des permissions de l'API utilisateur."""
    def setUp(self):
        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin_api',
            email='super_api@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )

        self.admin_org1 = User.objects.create_user(
            username='admin_org1_api',
            email='admin_org1_api@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.admin_org1.organizations.add(self.org1)

        self.admin_org2 = User.objects.create_user(
            username='admin_org2_api',
            email='admin_org2_api@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.admin_org2.organizations.add(self.org2)

        self.manager_org1 = User.objects.create_user(
            username='manager_org1_api',
            email='manager_org1_api@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        self.manager_org1.organizations.add(self.org1)

        self.employee1_org1 = User.objects.create_user(
            username='employee1_org1_api',
            email='employee1_org1_api@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee1_org1.organizations.add(self.org1)

        self.employee2_org1 = User.objects.create_user(
            username='employee2_org1_api',
            email='employee2_org1_api@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee2_org1.organizations.add(self.org1)

        self.employee_org2 = User.objects.create_user(
            username='employee_org2_api',
            email='employee_org2_api@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee_org2.organizations.add(self.org2)

        # Créer le client API
        self.client = APIClient()

    def authenticate_user(self, user):
        """Helper pour authentifier un utilisateur avec JWT."""
        # Obtenir le token JWT
        response = self.client.post('/api/v1/users/login/', {
            'email': user.email,
            'password': 'testpass123'
        })

        if response.status_code != 200:
            print(f"Échec de l'authentification pour {user.email}: {response.content}")
            raise AuthenticationFailed(f"Échec de l'authentification: {response.content}")

        self.assertEqual(response.status_code, 200)
        token = response.data['access']

        # Configurer le client avec le token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_can_list_organization_users(self):
        """Test qu'un admin peut lister tous les utilisateurs de son organisation."""
        # Authentifier l'admin avec JWT
        self.authenticate_user(self.admin_org1)

        # Faire la requête GET sur l'endpoint des utilisateurs
        response = self.client.get('/api/v1/users/')

        self.assertEqual(response.status_code, 200)
        users_data = response.json()

        # Vérifier que seuls les utilisateurs de org1 sont retournés
        user_employee_ids = [user['employee_id'] for user in users_data['results']]
        self.assertIn(self.manager_org1.employee_id, user_employee_ids)
        self.assertIn(self.employee1_org1.employee_id, user_employee_ids)
        self.assertIn(self.employee2_org1.employee_id, user_employee_ids)
        self.assertNotIn(self.employee_org2.employee_id, user_employee_ids)

    def test_admin_can_view_organization_user_detail(self):
        """Un admin doit pouvoir voir les détails des utilisateurs de son organisation"""
        # Authentifier l'admin avec JWT
        self.authenticate_user(self.admin_org1)

        # Tester l'accès aux détails d'un employé de son organisation
        response = self.client.get(f'/api/v1/users/{self.employee1_org1.id}/')
        self.assertEqual(response.status_code, 200)

        # Tester l'accès aux détails d'un employé d'une autre organisation
        response = self.client.get(f'/api/v1/users/{self.employee_org2.id}/')
        self.assertEqual(response.status_code, 403)

    def test_manager_can_view_organization_employees(self):
        """Un manager doit pouvoir voir les employés de son organisation"""
        # Authentifier le manager avec JWT
        self.authenticate_user(self.manager_org1)

        # Faire la requête GET sur l'endpoint des utilisateurs
        response = self.client.get('/api/v1/users/', {'role': 'EMPLOYEE'})

        self.assertEqual(response.status_code, 200)
        users_data = response.json()

        # Vérifier que seuls les employés sont retournés
        user_employee_ids = [user['employee_id'] for user in users_data['results']]
        self.assertIn(self.employee1_org1.employee_id, user_employee_ids)
        self.assertIn(self.employee2_org1.employee_id, user_employee_ids)
        self.assertNotIn(self.admin_org1.employee_id, user_employee_ids)
        self.assertNotIn(self.employee_org2.employee_id, user_employee_ids)

    def test_manager_can_view_employee_detail(self):
        """Un manager doit pouvoir voir les détails des employés de son organisation"""
        # Authentifier le manager avec JWT
        self.authenticate_user(self.manager_org1)

        # Tester l'accès aux détails d'un employé de son organisation
        response = self.client.get(f'/api/v1/users/{self.employee1_org1.id}/')
        self.assertEqual(response.status_code, 200)

        # Tester l'accès aux détails d'un admin
        response = self.client.get(f'/api/v1/users/{self.admin_org1.id}/')
        self.assertEqual(response.status_code, 403)

        # Tester l'accès aux détails d'un employé d'une autre organisation
        response = self.client.get(f'/api/v1/users/{self.employee_org2.id}/')
        self.assertEqual(response.status_code, 403)

    def test_employee_can_only_view_own_profile(self):
        """Un employé ne doit pouvoir voir que son propre profil"""
        # Authentifier l'employé avec JWT
        self.authenticate_user(self.employee1_org1)

        # Tester l'accès à son propre profil via l'endpoint profile
        response = self.client.get('/api/v1/users/profile/')
        self.assertEqual(response.status_code, 200)

        # Tester l'accès au profil d'un autre employé
        response = self.client.get(f'/api/v1/users/{self.employee2_org1.id}/')
        self.assertEqual(response.status_code, 403)

        # Tester l'accès au profil d'un manager
        response = self.client.get(f'/api/v1/users/{self.manager_org1.id}/')
        self.assertEqual(response.status_code, 403)

    def test_super_admin_can_view_all_users(self):
        """Un super admin doit pouvoir voir tous les utilisateurs"""
        # Authentifier le super admin avec JWT
        self.authenticate_user(self.super_admin)

        # Faire la requête GET sur l'endpoint des utilisateurs
        response = self.client.get('/api/v1/users/')

        self.assertEqual(response.status_code, 200)
        users_data = response.json()

        # Vérifier que tous les utilisateurs sont retournés
        user_employee_ids = [user['employee_id'] for user in users_data['results']]
        self.assertIn(self.admin_org1.employee_id, user_employee_ids)
        self.assertIn(self.manager_org1.employee_id, user_employee_ids)
        self.assertIn(self.employee1_org1.employee_id, user_employee_ids)
        self.assertIn(self.employee2_org1.employee_id, user_employee_ids)
        self.assertIn(self.employee_org2.employee_id, user_employee_ids)

    def test_user_creation_permissions(self):
        """Tester les permissions de création d'utilisateurs"""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'role': User.Role.EMPLOYEE,
            'organizations': [self.org1.id]
        }

        # Super admin peut créer n'importe quel utilisateur
        self.authenticate_user(self.super_admin)
        response = self.client.post('/api/v1/users/register/', user_data)
        self.assertEqual(response.status_code, 201)

        # Admin peut créer des utilisateurs dans son organisation
        self.authenticate_user(self.admin_org1)
        user_data['username'] = 'newuser2'
        user_data['email'] = 'newuser2@test.com'
        response = self.client.post('/api/v1/users/register/', user_data)
        self.assertEqual(response.status_code, 201)

        # Manager ne peut pas créer d'utilisateurs
        self.authenticate_user(self.manager_org1)
        user_data['username'] = 'newuser3'
        user_data['email'] = 'newuser3@test.com'
        response = self.client.post('/api/v1/users/register/', user_data)
        self.assertEqual(response.status_code, 403)

        # Employé ne peut pas créer d'utilisateurs
        self.authenticate_user(self.employee1_org1)
        user_data['username'] = 'newuser4'
        user_data['email'] = 'newuser4@test.com'
        response = self.client.post('/api/v1/users/register/', user_data)
        self.assertEqual(response.status_code, 403)

    def test_user_update_permissions(self):
        """Tester les permissions de modification d'utilisateurs"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        # Vérifier que tous les utilisateurs existent
        self.assertTrue(User.objects.filter(id=self.employee1_org1.id).exists())
        self.assertTrue(User.objects.filter(id=self.employee_org2.id).exists())
        self.assertTrue(User.objects.filter(id=self.admin_org1.id).exists())

        # Super admin peut modifier n'importe quel utilisateur
        self.authenticate_user(self.super_admin)
        response = self.client.patch(
            f'/api/v1/users/{self.employee1_org1.id}/', update_data)
        self.assertEqual(response.status_code, 200)

        # Admin peut modifier les utilisateurs de son organisation
        self.authenticate_user(self.admin_org1)
        response = self.client.patch(
            f'/api/v1/users/{self.employee1_org1.id}/', update_data)
        self.assertEqual(response.status_code, 200)

        # Admin ne peut pas modifier les utilisateurs d'autres organisations
        response = self.client.patch(
            f'/api/v1/users/{self.admin_org2.id}/', update_data)
        self.assertEqual(response.status_code, 403)

        # Manager peut modifier les employés de son organisation
        self.authenticate_user(self.manager_org1)
        response = self.client.patch(
            f'/api/v1/users/{self.employee1_org1.id}/', update_data)
        self.assertEqual(response.status_code, 200)

        # Manager ne peut pas modifier les admins ou autres managers
        response = self.client.patch(
            f'/api/v1/users/{self.admin_org1.id}/', update_data)
        self.assertEqual(response.status_code, 403)

        # Employé peut modifier son propre profil via l'endpoint profile
        self.authenticate_user(self.employee1_org1)
        response = self.client.patch('/api/v1/users/profile/', update_data)
        self.assertEqual(response.status_code, 200)

        # Employé ne peut pas modifier d'autres profils
        response = self.client.patch(
            f'/api/v1/users/{self.employee2_org1.id}/', update_data)
        self.assertEqual(response.status_code, 403)
