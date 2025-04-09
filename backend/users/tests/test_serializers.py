from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, RequestFactory
from rest_framework.exceptions import PermissionDenied
from users.serializers import UserSerializer

User = get_user_model()

class UserSerializerTests(TestCase):
    def setUp(self):
        """Initialisation des tests"""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = User.objects.create_user(
            username='admin',
            password='testpass123',
            role=User.Role.ADMIN
        )

    def test_reset_password(self):
        """Test la réinitialisation de mot de passe"""
        user = User.objects.create_user(
            username='testuser',
            password='oldpassword',
            email='test@example.com'
        )
        
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
        self.assertTrue(updated_user.check_password(updated_user.password))

    def test_reset_password_without_permission(self):
        """Test la réinitialisation de mot de passe sans permission"""
        user = User.objects.create_user(
            username='testuser',
            password='oldpassword',
            email='test@example.com'
        )
        
        # Créer un utilisateur sans permission
        self.request.user = User.objects.create_user(
            username='nopermission',
            password='testpass123',
            role=User.Role.EMPLOYEE
        )
        
        serializer = UserSerializer(
            instance=user,
            data={'reset_password': True},
            partial=True,
            context={'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(PermissionDenied):
            serializer.save()

    def test_reset_password_sends_email(self):
        """Test que l'email est envoyé lors de la réinitialisation de mot de passe"""
        user = User.objects.create_user(
            username='testuser',
            password='oldpassword',
            email='test@example.com'
        )
        
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
        self.assertIn('Votre mot de passe a été réinitialisé', mail.outbox[0].subject)
        self.assertIn(updated_user.password, mail.outbox[0].body) 