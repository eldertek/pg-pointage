from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from organizations.models import Organization
from users.permissions import HasUserPermission

User = get_user_model()

class UserPermissionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org1 = Organization.objects.create(name='Org1', org_id='O001')
        self.org2 = Organization.objects.create(name='Org2', org_id='O002')

def test_admin_can_reset_password_of_their_organization_users(self):
    """Test qu'un admin peut réinitialiser le mot de passe des utilisateurs de son organisation"""
    admin = User.objects.create_user(
        username='admin',
        password='testpass123',
        role=User.Role.ADMIN
    )
    admin.organizations.add(self.org1)

    user = User.objects.create_user(
        username='user',
        password='testpass123',
        role=User.Role.EMPLOYEE
    )
    user.organizations.add(self.org1)

    permission = HasUserPermission()
    request = self.factory.patch(f'/api/users/{user.id}/', {'reset_password': True})
    request.user = admin

    self.assertTrue(permission.has_object_permission(request, None, user))

def test_admin_cannot_reset_password_of_other_organization_users(self):
    """Test qu'un admin ne peut pas réinitialiser le mot de passe des utilisateurs d'autres organisations"""
    admin = User.objects.create_user(
        username='admin',
        password='testpass123',
        role=User.Role.ADMIN
    )
    admin.organizations.add(self.org1)

    user = User.objects.create_user(
        username='user',
        password='testpass123',
        role=User.Role.EMPLOYEE
    )
    user.organizations.add(self.org2)

    permission = HasUserPermission()
    request = self.factory.patch(f'/api/users/{user.id}/', {'reset_password': True})
    request.user = admin

    self.assertFalse(permission.has_object_permission(request, None, user))

def test_super_admin_can_reset_password_of_any_user(self):
    """Test qu'un super admin peut réinitialiser le mot de passe de n'importe quel utilisateur"""
    super_admin = User.objects.create_user(
        username='superadmin',
        password='testpass123',
        role=User.Role.SUPER_ADMIN
    )

    user = User.objects.create_user(
        username='user',
        password='testpass123',
        role=User.Role.EMPLOYEE
    )
    user.organizations.add(self.org1)

    permission = HasUserPermission()
    request = self.factory.patch(f'/api/users/{user.id}/', {'reset_password': True})
    request.user = super_admin

    self.assertTrue(permission.has_object_permission(request, None, user))

def test_manager_cannot_reset_password(self):
    """Test qu'un manager ne peut pas réinitialiser le mot de passe"""
    manager = User.objects.create_user(
        username='manager',
        password='testpass123',
        role=User.Role.MANAGER
    )
    manager.organizations.add(self.org1)

    user = User.objects.create_user(
        username='user',
        password='testpass123',
        role=User.Role.EMPLOYEE
    )
    user.organizations.add(self.org1)

    permission = HasUserPermission()
    request = self.factory.patch(f'/api/users/{user.id}/', {'reset_password': True})
    request.user = manager

    self.assertFalse(permission.has_object_permission(request, None, user))

def test_employee_cannot_reset_password(self):
    """Test qu'un employé ne peut pas réinitialiser le mot de passe"""
    employee = User.objects.create_user(
        username='employee',
        password='testpass123',
        role=User.Role.EMPLOYEE
    )
    employee.organizations.add(self.org1)

    user = User.objects.create_user(
        username='user',
        password='testpass123',
        role=User.Role.EMPLOYEE
    )
    user.organizations.add(self.org1)

    permission = HasUserPermission()
    request = self.factory.patch(f'/api/users/{user.id}/', {'reset_password': True})
    request.user = employee

    self.assertFalse(permission.has_object_permission(request, None, user)) 