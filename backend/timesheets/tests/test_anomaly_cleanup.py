"""
Tests pour la fonctionnalité de nettoyage des anomalies.

Ces tests vérifient que les anomalies de type "départ manquant" sont supprimées
lorsqu'un départ est enregistré entre-temps.
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

from organizations.models import Organization
from sites.models import Site
from timesheets.models import Timesheet, Anomaly
from alerts.models import Alert

User = get_user_model()


class AnomalyCleanupTestCase(TestCase):
    """Test case pour la fonctionnalité de nettoyage des anomalies."""

    def setUp(self):
        """Set up test data."""
        # Create organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            org_id='TST'
        )

        # Create site
        self.site = Site.objects.create(
            name='Test Site',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.organization,
            nfc_id='TST-S001',
            late_margin=10,
            early_departure_margin=10
        )

        # Create employee
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            first_name='Test',
            last_name='Employee'
        )

        # Add employee to organization
        self.employee.organizations.add(self.organization)

        # Set up a date for testing
        self.test_date = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def test_missing_departure_cleanup(self):
        """Test que les anomalies de départ manquant sont supprimées lorsqu'un départ est enregistré."""
        # Créer un pointage d'arrivée
        arrival_timestamp = self.test_date.replace(hour=9, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.NFC
        )

        # Créer une anomalie de départ manquant via l'API scan-anomalies
        # Créer un utilisateur manager pour l'authentification
        manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        manager.organizations.add(self.organization)
        
        client = APIClient()
        client.force_authenticate(user=manager)
        
        # Exécuter le scan d'anomalies pour créer l'anomalie de départ manquant
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.test_date.date(),
                'end_date': self.test_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.test_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Créer un pointage de départ
        departure_timestamp = self.test_date.replace(hour=17, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.NFC
        )

        # Exécuter à nouveau le scan d'anomalies pour nettoyer automatiquement l'anomalie
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.test_date.date(),
                'end_date': self.test_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)

        # Vérifier que l'anomalie a été supprimée automatiquement
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.test_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 0)

    def test_missing_arrival_cleanup(self):
        """Test que les anomalies d'arrivée manquante sont supprimées lorsqu'une arrivée est enregistrée."""
        # Créer un utilisateur manager pour l'authentification
        manager = User.objects.create_user(
            username='manager2',
            email='manager2@test.com',
            password='testpass123',
            role=User.Role.MANAGER
        )
        manager.organizations.add(self.organization)
        
        client = APIClient()
        client.force_authenticate(user=manager)
        
        # On simule un cas où un employé a un départ sans arrivée
        # Créer un pointage de départ sans arrivée correspondante
        departure_timestamp = self.test_date.replace(hour=17, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.NFC
        )
        
        # Exécuter le scan d'anomalies pour créer l'anomalie d'arrivée manquante
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.test_date.date(),
                'end_date': self.test_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.test_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)

        # Créer un pointage d'arrivée
        arrival_timestamp = self.test_date.replace(hour=9, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.NFC
        )

        # Exécuter à nouveau le scan d'anomalies pour nettoyer automatiquement l'anomalie
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.test_date.date(),
                'end_date': self.test_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)

        # Vérifier que l'anomalie a été supprimée automatiquement
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.test_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 0)
