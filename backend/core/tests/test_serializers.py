"""Test des mixins de permissions pour les serializers"""
from django.test import TestCase
from rest_framework import serializers
from users.models import User
from organizations.models import Organization
from sites.models import Site
from core.mixins import OrganizationPermissionMixin, SitePermissionMixin
from types import SimpleNamespace
from rest_framework.test import APIClient


class TestOrganizationSerializerMixin(serializers.Serializer, OrganizationPermissionMixin):
    """Serializer de test pour tester le mixin d'organisation"""
    organization_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        if 'organization_id' in attrs:
            self.validate_organization(attrs['organization_id'])
        return attrs

    def create(self, validated_data):
        pass  # Non utilisé dans les tests

    def update(self, instance, validated_data):
        pass  # Non utilisé dans les tests


class TestSiteSerializerMixin(serializers.Serializer, SitePermissionMixin):
    """Serializer de test pour tester le mixin de site"""
    site = serializers.PrimaryKeyRelatedField(
        queryset=Site.objects.all(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer le queryset en fonction de l'utilisateur
        if 'context' in kwargs and 'request' in kwargs['context']:
            user = kwargs['context']['request'].user
            if user.is_super_admin:
                self.fields['site'].queryset = Site.objects.all()
            else:
                self.fields['site'].queryset = Site.objects.filter(
                    organization__in=user.organizations.all()
                )

    def validate(self, attrs):
        if 'site' in attrs:
            self.validate_site(attrs['site'])
        return attrs

    def create(self, validated_data):
        pass  # Non utilisé dans les tests

    def update(self, instance, validated_data):
        pass  # Non utilisé dans les tests


class TestOrganizationPermissionTests(TestCase):
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

        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization 1',
            org_id='O001'
        )
        self.org2 = Organization.objects.create(
            name='Organization 2',
            org_id='O002'
        )

        # Associer l'admin à l'organisation 1
        self.admin.organizations.add(self.org1)

    def test_organization_validation_super_admin(self):
        """Test que le super admin peut accéder à toutes les organisations"""
        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org1.id},
            context={'request': SimpleNamespace(user=self.super_admin)}
        )
        self.assertTrue(serializer.is_valid())

        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org2.id},
            context={'request': SimpleNamespace(user=self.super_admin)}
        )
        self.assertTrue(serializer.is_valid())

    def test_organization_validation_admin(self):
        """Test que l'admin ne peut accéder qu'à ses organisations"""
        # Test accès autorisé
        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org1.id},
            context={'request': SimpleNamespace(user=self.admin)}
        )
        self.assertTrue(serializer.is_valid())

        # Test accès non autorisé
        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org2.id},
            context={'request': SimpleNamespace(user=self.admin)}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('organization', serializer.errors)


class TestSitePermissionMixinDirect(SitePermissionMixin):
    """Version simplifiée du mixin pour tester directement les méthodes"""

    def __init__(self, user):
        self.context = {'request': SimpleNamespace(user=user)}


class TestSitePermissionTests(TestCase):
    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin_direct',
            email='super_direct@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            username='admin_direct',
            email='admin_direct@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )

        # Créer les organisations
        self.org1 = Organization.objects.create(
            name='Organization Direct 1',
            org_id='OD01'
        )
        self.org2 = Organization.objects.create(
            name='Organization Direct 2',
            org_id='OD02'
        )

        # Associer l'admin à l'organisation 1
        self.admin.organizations.add(self.org1)

        # Créer les sites
        self.site1 = Site.objects.create(
            name='Site Direct 1',
            address='123 Test Direct St',
            postal_code='75000',
            city='Paris',
            organization=self.org1,
            nfc_id='OD01-S01'
        )
        self.site2 = Site.objects.create(
            name='Site Direct 2',
            address='456 Test Direct Ave',
            postal_code='75001',
            city='Paris',
            organization=self.org2,
            nfc_id='OD02-S01'
        )

    def test_site_permission_super_admin(self):
        """Test que le super admin peut accéder à tous les sites"""
        mixin = TestSitePermissionMixinDirect(self.super_admin)

        # Le super admin peut accéder à tous les sites
        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertTrue(mixin.has_site_permission(self.site2))

        # La validation ne doit pas lever d'exception
        mixin.validate_site(self.site1)
        mixin.validate_site(self.site2)

    def test_site_permission_admin(self):
        """Test que l'admin ne peut accéder qu'aux sites de ses organisations"""
        mixin = TestSitePermissionMixinDirect(self.admin)

        # L'admin peut accéder aux sites de son organisation
        self.assertTrue(mixin.has_site_permission(self.site1))
        self.assertFalse(mixin.has_site_permission(self.site2))

        # La validation ne doit pas lever d'exception pour les sites autorisés
        mixin.validate_site(self.site1)

        # La validation doit lever une exception pour les sites non autorisés
        with self.assertRaises(serializers.ValidationError):
            mixin.validate_site(self.site2)


class TestUserCreationPermissionTests(TestCase):
    """Tests des permissions pour la création d'utilisateurs"""

    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin_user',
            email='super_user@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )

        # Créer des organisations
        self.org1 = Organization.objects.create(
            name='Organization User 1',
            org_id='OU01'
        )
        self.org2 = Organization.objects.create(
            name='Organization User 2',
            org_id='OU02'
        )

        # Créer un admin associé à l'organisation 1
        self.admin = User.objects.create_user(
            username='admin_user',
            email='admin_user@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.admin.organizations.add(self.org1)

    def test_admin_cannot_create_super_admin(self):
        """Test qu'un admin ne peut pas créer un super admin"""
        from users.serializers import UserSerializer

        # Préparer les données pour un nouvel utilisateur super admin
        user_data = {
            'username': 'new_super_admin',
            'email': 'new_super@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'SuperAdmin',
            'role': User.Role.SUPER_ADMIN,
            'organizations': [self.org1.id],
            'phone_number': '0123456789',
        }

        # Créer un serializer avec l'admin comme utilisateur authentifié
        serializer = UserSerializer(
            data=user_data,
            context={'request': SimpleNamespace(user=self.admin)}
        )

        # La validation doit échouer car un admin ne peut pas créer un super admin
        self.assertFalse(serializer.is_valid())

    def test_admin_can_create_manager_in_own_organization(self):
        """Test qu'un admin peut créer un manager dans sa propre organisation"""
        from users.serializers import UserSerializer

        # Préparer les données pour un nouvel utilisateur manager
        user_data = {
            'username': 'new_manager',
            'email': 'new_manager@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Manager',
            'role': User.Role.MANAGER,
            'organizations': [self.org1.id],
            'phone_number': '0123456789',
        }

        # Créer un serializer avec l'admin comme utilisateur authentifié
        serializer = UserSerializer(
            data=user_data,
            context={'request': SimpleNamespace(user=self.admin)}
        )

        # La validation doit réussir car un admin peut créer un manager dans son organisation
        self.assertTrue(serializer.is_valid())

    def test_admin_cannot_create_user_in_other_organization(self):
        """Test qu'un admin ne peut pas créer d'utilisateur dans une autre organisation"""
        from users.serializers import UserSerializer

        # Préparer les données pour un nouvel utilisateur employé dans une autre organisation
        user_data = {
            'username': 'new_employee',
            'email': 'new_employee@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Employee',
            'role': User.Role.EMPLOYEE,
            # Organisation à laquelle l'admin n'appartient pas
            'organizations': [self.org2.id],
            'phone_number': '0123456789',
        }

        # Créer un serializer avec l'admin comme utilisateur authentifié
        serializer = UserSerializer(
            data=user_data,
            context={'request': SimpleNamespace(user=self.admin)}
        )

        # La validation doit échouer car un admin ne peut pas créer d'utilisateur dans une autre organisation
        self.assertFalse(serializer.is_valid())
        self.assertIn('organizations', serializer.errors)

    def test_admin_can_create_employee_in_own_organization(self):
        """Test qu'un admin peut créer un employé dans sa propre organisation"""
        from users.serializers import UserSerializer

        # Préparer les données pour un nouvel utilisateur employé
        user_data = {
            'username': 'new_employee',
            'email': 'new_employee@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Employee',
            'role': User.Role.EMPLOYEE,
            'organizations': [self.org1.id],
            'phone_number': '0123456789',
        }

        # Créer un serializer avec l'admin comme utilisateur authentifié
        serializer = UserSerializer(
            data=user_data,
            context={'request': SimpleNamespace(user=self.admin)}
        )

        # La validation doit réussir car un admin peut créer un employé dans son organisation
        self.assertTrue(serializer.is_valid())


class TestViewsFilteringTests(TestCase):
    """Tests pour vérifier que les vues filtrent correctement selon les permissions"""

    def setUp(self):
        # Créer les utilisateurs
        self.super_admin = User.objects.create_user(
            username='super_admin_views',
            email='super_views@test.com',
            password='testpass123',
            role=User.Role.SUPER_ADMIN
        )

        self.admin1 = User.objects.create_user(
            username='admin1_views',
            email='admin1_views@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )

        self.admin2 = User.objects.create_user(
            username='admin2_views',
            email='admin2_views@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )

        # Créer des organisations
        self.org1 = Organization.objects.create(
            name='Organization View 1',
            org_id='OV01'
        )
        self.org2 = Organization.objects.create(
            name='Organization View 2',
            org_id='OV02'
        )

        # Associer les admins à leurs organisations respectives
        self.admin1.organizations.add(self.org1)
        self.admin2.organizations.add(self.org2)

        # Créer des employés pour chaque organisation
        self.employee1 = User.objects.create_user(
            username='employee1_views',
            email='employee1_views@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee1.organizations.add(self.org1)

        self.employee2 = User.objects.create_user(
            username='employee2_views',
            email='employee2_views@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.employee2.organizations.add(self.org2)

    def test_organization_view_filtering(self):
        """Test que la vue OrganizationListView filtre correctement selon les permissions"""
        from organizations.views import OrganizationListView

        # Le super admin doit voir toutes les organisations
        view = OrganizationListView()
        view.request = type('Request', (), {'user': self.super_admin})
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)

        # Admin1 ne doit voir que son organisation (org1)
        view = OrganizationListView()
        view.request = type('Request', (), {'user': self.admin1})
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().id, self.org1.id)

        # Admin2 ne doit voir que son organisation (org2)
        view = OrganizationListView()
        view.request = type('Request', (), {'user': self.admin2})
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().id, self.org2.id)

    def test_user_view_filtering(self):
        """Test que la vue UserListView filtre correctement selon les permissions"""
        from users.views import UserListView

        # Le super admin doit voir tous les utilisateurs
        view = UserListView()
        view.request = type(
            'Request', (), {'user': self.super_admin, 'query_params': {}})
        queryset = view.get_queryset()
        # super_admin, admin1, admin2, employee1, employee2
        self.assertEqual(queryset.count(), 5)

        # Admin1 doit voir uniquement les utilisateurs de son organisation (lui-même et employee1)
        view = UserListView()
        view.request = type(
            'Request', (), {'user': self.admin1, 'query_params': {}})
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)
        user_ids = [user.id for user in queryset]
        self.assertIn(self.admin1.id, user_ids)
        self.assertIn(self.employee1.id, user_ids)

        # Employee1 ne doit voir que lui-même
        view = UserListView()
        view.request = type(
            'Request', (), {'user': self.employee1, 'query_params': {}})
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().id, self.employee1.id)


class TestUserRegisterSerializerRestrictions(TestCase):
    """Tests pour vérifier les restrictions de création d'utilisateurs avec UserRegisterSerializer"""

    def setUp(self):
        # Créer un super admin
        self.super_admin = User.objects.create_user(
            username="superadmin",
            email="superadmin@example.com",
            password="password123",
            role=User.Role.SUPER_ADMIN,
            is_active=True
        )

        # Créer une organisation
        self.org1 = Organization.objects.create(name="Organisation 1")

        # Créer un admin dans cette organisation
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="password123",
            role=User.Role.ADMIN,
            is_active=True
        )
        self.admin.organizations.add(self.org1)

        # Initialiser le client API
        self.client = APIClient()

    def test_admin_cannot_create_super_admin(self):
        """Un admin ne devrait pas pouvoir créer un super admin"""
        # Connecter l'admin
        self.client.force_authenticate(user=self.admin)
        
        # Données pour créer un super admin
        data = {
            "username": "newsuperadmin",
            "email": "newsuperadmin@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "SuperAdmin",
            "role": User.Role.SUPER_ADMIN,
            "organizations": [self.org1.id]
        }
        
        # Envoyer la requête pour créer un utilisateur
        response = self.client.post("/api/v1/users/register/", data, format="json")
        
        # Vérifier que la création a échoué
        self.assertEqual(response.status_code, 400)
        self.assertIn("role", response.data)
    
    def test_super_admin_can_create_super_admin(self):
        """Un super admin devrait pouvoir créer un autre super admin"""
        # Connecter le super admin
        self.client.force_authenticate(user=self.super_admin)
        
        # Données pour créer un super admin
        data = {
            "username": "newsuperadmin",
            "email": "newsuperadmin@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "SuperAdmin",
            "role": User.Role.SUPER_ADMIN,
            "organizations": [self.org1.id]
        }
        
        # Envoyer la requête pour créer un utilisateur
        response = self.client.post("/api/v1/users/register/", data, format="json")
        
        # Vérifier que la création a réussi
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.filter(username="newsuperadmin", role=User.Role.SUPER_ADMIN).count(), 1)
    
    def test_admin_can_create_employees_and_managers(self):
        """Un admin devrait pouvoir créer des employés et des managers"""
        # Connecter l'admin
        self.client.force_authenticate(user=self.admin)
        
        # Cas 1: Créer un employé
        employee_data = {
            "username": "newemployee",
            "email": "newemployee@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "Employee",
            "role": User.Role.EMPLOYEE,
            "organizations": [self.org1.id]
        }
        
        response = self.client.post("/api/v1/users/register/", employee_data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.filter(username="newemployee", role=User.Role.EMPLOYEE).count(), 1)
        
        # Cas 2: Créer un manager
        manager_data = {
            "username": "newmanager",
            "email": "newmanager@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "Manager",
            "role": User.Role.MANAGER,
            "organizations": [self.org1.id]
        }
        
        response = self.client.post("/api/v1/users/register/", manager_data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.filter(username="newmanager", role=User.Role.MANAGER).count(), 1)
