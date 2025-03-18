from django.test import TestCase, Client
from django.urls import reverse
from core.models import Site, User
from django.contrib.auth import get_user_model

class AutocompleteViewsTest(TestCase):
    def setUp(self):
        # Créer un superutilisateur pour les tests
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        
        # Créer des données de test
        self.site1 = Site.objects.create(name='Site Test 1', address='Adresse 1')
        self.site2 = Site.objects.create(name='Site Test 2', address='Adresse 2')
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='userpass1',
            first_name='Prénom1',
            last_name='Nom1'
        )
        
        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_site_autocomplete_success(self):
        """Test la recherche de sites avec un terme valide"""
        url = reverse('site-autocomplete')
        response = self.client.get(url, {'term': 'Site'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertTrue(any(item['name'] == 'Site Test 1' for item in data))

    def test_site_autocomplete_validation(self):
        """Test la validation des termes de recherche pour les sites"""
        url = reverse('site-autocomplete')
        
        # Test avec un terme trop court
        response = self.client.get(url, {'term': ''})
        self.assertEqual(response.status_code, 400)
        
        # Test avec des caractères spéciaux
        response = self.client.get(url, {'term': '<script>'})
        self.assertEqual(response.status_code, 400)

    def test_user_autocomplete_success(self):
        """Test la recherche d'utilisateurs avec un terme valide"""
        url = reverse('user-autocomplete')
        response = self.client.get(url, {'term': 'user'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)
        self.assertTrue(any(item['username'] == 'user1' for item in data))

    def test_user_autocomplete_format(self):
        """Test le format des résultats pour les utilisateurs"""
        url = reverse('user-autocomplete')
        response = self.client.get(url, {'term': 'user1'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        user_data = data[0]
        
        self.assertIn('id', user_data)
        self.assertIn('username', user_data)
        self.assertIn('full_name', user_data)
        self.assertEqual(user_data['username'], 'user1')
        self.assertEqual(user_data['full_name'], 'Prénom1 Nom1')

    def test_max_results_limit(self):
        """Test la limitation du nombre de résultats"""
        # Créer plus de sites que la limite
        for i in range(15):
            Site.objects.create(name=f'Site Test {i+3}')
            
        url = reverse('site-autocomplete')
        response = self.client.get(url, {'term': 'Site'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 10)  # max_results est défini à 10

    def test_error_handling(self):
        """Test la gestion des erreurs"""
        url = reverse('site-autocomplete')
        
        # Test avec une requête malformée
        response = self.client.get(url, {'invalid_param': 'value'})
        self.assertEqual(response.status_code, 400)
        
        # Test avec un terme de recherche invalide
        response = self.client.get(url, {'term': '<>'})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data) 