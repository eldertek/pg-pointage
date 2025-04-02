import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from organizations.models import Organization
from sites.models import Site
from sites.models import SiteEmployee

class TestViewMixin(TestCase):
    def setUp(self):
        self.client = APIClient()
        
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

        # Créer les associations site-employé
        SiteEmployee.objects.create(
            site=self.site1,
            employee=self.employee,
            is_active=True
        )
        SiteEmployee.objects.create(
            site=self.site1,
            employee=self.manager,
            is_active=True
        )

    def test_authentication_required(self):
        """Test que l'authentification est requise pour accéder aux vues"""
        # Test sans authentification
        response = self.client.get('/api/v1/organizations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test avec authentification
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/organizations/')
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_organization_access_super_admin(self):
        """Test que le super admin peut accéder à toutes les organisations"""
        self.client.force_authenticate(user=self.super_admin)
        
        # Test accès à l'organisation 1
        response = self.client.get(f'/api/v1/organizations/{self.org1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test accès à l'organisation 2
        response = self.client.get(f'/api/v1/organizations/{self.org2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_organization_access_admin(self):
        """Test que l'admin ne peut accéder qu'à ses organisations"""
        self.client.force_authenticate(user=self.admin)
        
        # Test accès autorisé
        response = self.client.get(f'/api/v1/organizations/{self.org1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test accès non autorisé
        response = self.client.get(f'/api/v1/organizations/{self.org2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_site_access_super_admin(self):
        """Test que le super admin peut accéder à tous les sites"""
        self.client.force_authenticate(user=self.super_admin)
        
        # Test accès au site 1
        response = self.client.get(f'/api/v1/sites/{self.site1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test accès au site 2
        response = self.client.get(f'/api/v1/sites/{self.site2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_site_access_admin(self):
        """Test que l'admin ne peut accéder qu'aux sites de ses organisations"""
        self.client.force_authenticate(user=self.admin)
        
        # Test accès autorisé
        response = self.client.get(f'/api/v1/sites/{self.site1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test accès non autorisé
        response = self.client.get(f'/api/v1/sites/{self.site2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_site_access(self):
        """Test que le manager ne peut accéder qu'aux sites de son organisation"""
        self.client.force_authenticate(user=self.manager)
        
        # Test accès autorisé
        response = self.client.get(f'/api/v1/sites/{self.site1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test accès non autorisé
        response = self.client.get(f'/api/v1/sites/{self.site2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_site_access(self):
        """Test que l'employé ne peut accéder qu'aux sites auxquels il est assigné"""
        self.client.force_authenticate(user=self.employee)
        
        # Test accès autorisé
        response = self.client.get(f'/api/v1/sites/{self.site1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test accès non autorisé
        response = self.client.get(f'/api/v1/sites/{self.site2.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 