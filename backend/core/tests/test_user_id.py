"""Tests pour la génération d'ID utilisateur"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import User
from users.utils import validate_user_id, generate_user_id
from organizations.models import Organization
import concurrent.futures


class TestUserIDGeneration(TestCase):
    """Tests pour la génération et validation des IDs utilisateur"""

    def setUp(self):
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name="Test Organization",
            org_id="TST1"
        )
        # Nettoyer la base de données avant chaque test
        User.objects.all().delete()

    def test_validate_user_id(self):
        """Test la validation du format d'ID utilisateur"""
        self.assertTrue(validate_user_id('U00001'))
        self.assertTrue(validate_user_id('U99999'))
        self.assertFalse(validate_user_id('U00000'))
        self.assertFalse(validate_user_id('U100000'))
        self.assertFalse(validate_user_id('A00001'))
        self.assertFalse(validate_user_id('U0001'))
        self.assertFalse(validate_user_id('U000001'))

    def test_generate_user_id(self):
        """Test la génération d'ID utilisateur"""
        # Vérifier que la base de données est vide
        self.assertEqual(User.objects.count(), 0)
        
        # Créer un premier utilisateur
        user1 = User.objects.create(
            username='user1',
            email='test1@example.com',
            first_name='Test1',
            last_name='User1'
        )
        self.assertEqual(user1.employee_id, 'U00001')
        
        # Créer un deuxième utilisateur
        user2 = User.objects.create(
            username='user2',
            email='test2@example.com',
            first_name='Test2',
            last_name='User2'
        )
        self.assertEqual(user2.employee_id, 'U00002')
        
        # Créer un utilisateur avec un ID manuel
        user3 = User.objects.create(
            username='user3',
            email='test3@example.com',
            first_name='Test3',
            last_name='User3',
            employee_id='U00005'
        )
        self.assertEqual(user3.employee_id, 'U00005')
        
        # Le prochain ID devrait être U00006
        user4 = User.objects.create(
            username='user4',
            email='test4@example.com',
            first_name='Test4',
            last_name='User4'
        )
        self.assertEqual(user4.employee_id, 'U00006')

    def test_generate_user_id_with_invalid_existing(self):
        """Test la génération d'ID avec des IDs invalides existants"""
        # Créer un utilisateur avec un ID invalide
        user = User.objects.create(
            username='user1',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            employee_id='INVALID'
        )
        # L'ID devrait être corrigé automatiquement
        self.assertTrue(validate_user_id(user.employee_id))
        self.assertEqual(user.employee_id, 'U00001')

    def test_generate_user_id_with_max_value(self):
        """Test la génération d'ID avec le maximum atteint"""
        # Créer un utilisateur avec l'ID maximum
        user = User.objects.create(
            username='user1',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            employee_id='U99999'
        )
        self.assertEqual(user.employee_id, 'U99999')
        
        # Essayer de créer un autre utilisateur devrait échouer
        with self.assertRaises(ValueError):
            User.objects.create(
                username='user2',
                email='test2@example.com',
                first_name='Test2',
                last_name='User2'
            )

    def test_update_user_with_invalid_id(self):
        """Test la mise à jour d'un utilisateur avec un ID invalide"""
        user = User.objects.create(
            username='user1',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        user.employee_id = 'INVALID'
        user.save()
        # L'ID devrait être corrigé automatiquement
        self.assertTrue(validate_user_id(user.employee_id))

    def test_concurrent_user_creation(self):
        """Test la création concurrente d'utilisateurs"""
        def create_random_user(_):
            user = User.objects.create(
                username=f'user{_}',
                email=f'test{_}@example.com',
                first_name=f'Test{_}',
                last_name=f'User{_}'
            )
            user.organizations.add(self.organization)
            return user.employee_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            user_ids = list(executor.map(create_random_user, range(10)))

        # Vérifier que tous les IDs sont uniques
        self.assertEqual(len(set(user_ids)), 10)
        # Vérifier que tous les IDs sont valides
        for user_id in user_ids:
            self.assertTrue(validate_user_id(user_id)) 