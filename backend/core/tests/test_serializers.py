"""Test des mixins de permissions pour les serializers"""
from django.test import TestCase
from rest_framework import serializers
from users.models import User
from organizations.models import Organization
from sites.models import Site
from core.mixins import OrganizationPermissionMixin, SitePermissionMixin


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
            context={'request': type(
                'Request', (), {'user': self.super_admin})}
        )
        self.assertTrue(serializer.is_valid())

        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org2.id},
            context={'request': type(
                'Request', (), {'user': self.super_admin})}
        )
        self.assertTrue(serializer.is_valid())

    def test_organization_validation_admin(self):
        """Test que l'admin ne peut accéder qu'à ses organisations"""
        # Test accès autorisé
        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org1.id},
            context={'request': type('Request', (), {'user': self.admin})}
        )
        self.assertTrue(serializer.is_valid())

        # Test accès non autorisé
        serializer = TestOrganizationSerializerMixin(
            data={'organization_id': self.org2.id},
            context={'request': type('Request', (), {'user': self.admin})}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('organization', serializer.errors)


class TestSitePermissionTests(TestCase):
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

        # Créer les sites
        self.site1 = Site.objects.create(
            name='Site 1',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.org1,
            nfc_id='O001-S001'
        )
        self.site2 = Site.objects.create(
            name='Site 2',
            address='456 Test Ave',
            postal_code='75001',
            city='Paris',
            organization=self.org2,
            nfc_id='O002-S001'
        )

    def test_site_validation_super_admin(self):
        """Test que le super admin peut accéder à tous les sites"""
        # Créer un mock de request avec un super admin
        mock_user = type('User', (), {
            'is_super_admin': True,
            'organizations': type('Manager', (), {'all': lambda: []})()
        })
        mock_request = type('Request', (), {'user': mock_user})

        serializer = TestSiteSerializerMixin(
            data={'site': self.site1.id},
            context={'request': mock_request}
        )
        self.assertTrue(serializer.is_valid())

        serializer = TestSiteSerializerMixin(
            data={'site': self.site2.id},
            context={'request': mock_request}
        )
        self.assertTrue(serializer.is_valid())

    def test_site_validation_admin(self):
        """Test que l'admin ne peut accéder qu'aux sites de ses organisations"""
        # Créer un mock de request avec un admin
        mock_user = type('User', (), {
            'is_super_admin': False,
            'organizations': type('Manager', (), {'all': lambda: [self.org1]})()
        })
        mock_request = type('Request', (), {'user': mock_user})

        # Test accès autorisé
        serializer = TestSiteSerializerMixin(
            data={'site': self.site1.id},
            context={'request': mock_request}
        )
        print(
            f"[DEBUG] Test accès autorisé - site1: {self.site1.id}, org1: {self.org1.id}")
        print(
            f"[DEBUG] Mock user organizations: {[org.id for org in mock_user.organizations.all()]}")
        self.assertTrue(serializer.is_valid())

        # Test accès non autorisé
        serializer = TestSiteSerializerMixin(
            data={'site': self.site2.id},
            context={'request': mock_request}
        )
        print(
            f"[DEBUG] Test accès non autorisé - site2: {self.site2.id}, org2: {self.org2.id}")
        self.assertFalse(serializer.is_valid())
        self.assertIn('site', serializer.errors)
