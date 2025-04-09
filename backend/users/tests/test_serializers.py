from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, RequestFactory
from rest_framework.exceptions import ValidationError
from users.serializers import UserSerializer
from organizations.models import Organization

User = get_user_model()

class UserSerializerTests(TestCase):
    def setUp(self):
        """Initialisation des tests"""
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name='Test Org', org_id='T001')
        self.request = self.factory.get('/')
        self.request.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.request.user.organizations.add(self.org)

    def test_reset_password(self):
        """Test la réinitialisation de mot de passe"""
        # Créer un utilisateur dans la même organisation que l'admin
        user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='oldpassword'
        )
        user.organizations.add(self.org)
        
        serializer = UserSerializer(
            instance=user,
            data={'reset_password': True},
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Vérifie que le mot de passe a été changé
        self.assertFalse(updated_user.check_password('oldpassword'))
        # Le mot de passe a été changé (on ne peut pas vérifier la valeur exacte car il est haché)

    def test_reset_password_without_permission(self):
        """Test la réinitialisation de mot de passe sans permission"""
        # Créer un utilisateur dans une autre organisation
        other_org = Organization.objects.create(name='Other Org', org_id='O002')
        user = User.objects.create_user(
            username='testuser',
            email='testuser2@test.com',
            password='oldpassword'
        )
        user.organizations.add(other_org)
        
        # Créer un utilisateur sans permission
        self.request.user = User.objects.create_user(
            username='nopermission',
            email='nopermission@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        self.request.user.organizations.add(self.org)
        
        serializer = UserSerializer(
            instance=user,
            data={'reset_password': True},
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(ValidationError):
            serializer.save()

    def test_reset_password_sends_email(self):
        """Test que l'email est envoyé lors de la réinitialisation de mot de passe"""
        # Créer un utilisateur dans la même organisation que l'admin
        user = User.objects.create_user(
            username='testuser',
            email='testuser3@test.com',
            password='oldpassword'
        )
        user.organizations.add(self.org)
        
        serializer = UserSerializer(
            instance=user,
            data={'reset_password': True},
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Vérifie qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertIn('Réinitialisation de votre mot de passe', mail.outbox[0].subject)
        # On vérifie juste que le corps de l'email contient le mot "mot de passe"
        self.assertIn('mot de passe', mail.outbox[0].body.lower())

    def test_update_user_without_password(self):
        """Test la mise à jour d'un utilisateur sans modifier le mot de passe"""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='oldpassword'
        )
        user.organizations.add(self.org)
        
        serializer = UserSerializer(
            instance=user,
            data={
                'first_name': 'Nouveau',
                'last_name': 'Nom'
            },
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Vérifie que le mot de passe n'a pas été changé
        self.assertTrue(updated_user.check_password('oldpassword'))
        self.assertEqual(updated_user.first_name, 'Nouveau')
        self.assertEqual(updated_user.last_name, 'Nom')

    def test_update_user_with_password(self):
        """Test la mise à jour d'un utilisateur avec un nouveau mot de passe"""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='oldpassword'
        )
        user.organizations.add(self.org)
        
        serializer = UserSerializer(
            instance=user,
            data={
                'first_name': 'Nouveau',
                'last_name': 'Nom',
                'password': 'newpassword123'
            },
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Vérifie que le mot de passe a été changé
        self.assertFalse(updated_user.check_password('oldpassword'))
        self.assertTrue(updated_user.check_password('newpassword123'))
        self.assertEqual(updated_user.first_name, 'Nouveau')
        self.assertEqual(updated_user.last_name, 'Nom')

    def test_update_user_with_empty_password(self):
        """Test la mise à jour d'un utilisateur avec un mot de passe vide"""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='oldpassword'
        )
        user.organizations.add(self.org)
        
        serializer = UserSerializer(
            instance=user,
            data={
                'first_name': 'Nouveau',
                'last_name': 'Nom',
                'password': ''
            },
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Vérifie que le mot de passe n'a pas été changé
        self.assertTrue(updated_user.check_password('oldpassword'))
        self.assertEqual(updated_user.first_name, 'Nouveau')
        self.assertEqual(updated_user.last_name, 'Nom') 