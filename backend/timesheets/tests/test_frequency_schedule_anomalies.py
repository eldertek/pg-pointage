"""
Tests for anomalies related to frequency schedules.

These tests verify the detection and handling of anomalies for employees with frequency schedules,
including insufficient duration, single clock-ins, and missed clock-ins.
"""
from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from organizations.models import Organization
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from timesheets.models import Timesheet, Anomaly
from alerts.models import Alert

User = get_user_model()


class FrequencyScheduleAnomalyTestCase(TestCase):
    """Test case for anomalies related to frequency schedules.

    These tests focus on the workflows described in the requirements:
    - Workflow 9: Normal passage with compliant duration
    - Workflow 10: Passage with insufficient duration
    - Workflow 11: Single clock-in only
    - Workflow 12: No clock-ins
    """

    def setUp(self):
        """Set up test data."""
        # Create organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            org_id='TST'
        )
        
        # Create second organization for testing pointage sur site non rattaché
        self.organization2 = Organization.objects.create(
            name='Test Organization 2',
            org_id='TST2'
        )

        # Create site with frequency tolerance of 10%
        self.site = Site.objects.create(
            name='Test Site',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.organization,
            nfc_id='TST-S001',
            frequency_tolerance=10
        )
        
        # Create another site for testing
        self.site2 = Site.objects.create(
            name='Test Site 2',
            address='456 Test St',
            postal_code='75001',
            city='Paris',
            organization=self.organization,
            nfc_id='TST-S002',
            frequency_tolerance=10
        )
        
        # Create a site in another organization
        self.site3 = Site.objects.create(
            name='Test Site Other Org',
            address='789 Test St',
            postal_code='75002',
            city='Paris',
            organization=self.organization2,
            nfc_id='TST2-S001',
            frequency_tolerance=10
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
        self.employee.organizations.add(self.organization)

        # Create manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER,
            first_name='Test',
            last_name='Manager'
        )
        self.manager.organizations.add(self.organization)

        # Associate employee with site
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            is_active=True
        )

        # Create frequency schedule for Tuesday (90 minutes duration)
        self.schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )

        # Tuesday schedule (day_of_week=1)
        ScheduleDetail.objects.create(
            schedule=self.schedule,
            day_of_week=1,  # Tuesday
            frequency_duration=90
        )

        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.schedule,
            is_active=True
        )

        # Set up a Tuesday date for testing
        self.tuesday_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Ensure it's a Tuesday
        while self.tuesday_date.weekday() != 1:  # 1 is Tuesday
            self.tuesday_date += timedelta(days=1)

    def test_normal_passage(self):
        """Test Workflow 9: Normal passage with compliant duration."""
        # Employee clocks in at 9:00
        arrival_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Employee clocks out at 10:35 (95 minutes later, which is compliant)
        departure_timestamp = self.tuesday_date.replace(hour=10, minute=35)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Verify both timesheets are created correctly
        self.assertEqual(arrival_timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertEqual(departure_timesheet.entry_type, Timesheet.EntryType.DEPARTURE)

        # Verify no anomalies are created (duration > 90 minutes)
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date()
        )
        self.assertEqual(anomalies.count(), 0)

    def test_insufficient_duration(self):
        """Test Workflow 10: Passage with insufficient duration."""
        # Employee clocks in at 8:15
        arrival_timestamp = self.tuesday_date.replace(hour=8, minute=15)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Employee clocks out at 9:00 (45 minutes later, which is insufficient)
        departure_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Appeler l'API pour détecter les anomalies automatiquement
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['anomalies_created'], 0)

        # Verify anomaly is created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertEqual(anomalies.first().minutes, 45)

        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_duration_anomaly(self):
        """Test for frequency duration anomaly detection.

        This test verifies that an anomaly is created when the duration between
        arrival and departure doesn't match the expected frequency duration.
        """
        # Set up a frequency schedule with 30 minutes duration
        # First, delete the existing schedule detail
        from sites.models import ScheduleDetail
        ScheduleDetail.objects.filter(schedule=self.schedule).delete()

        # Create a new schedule detail with 30 minutes duration
        ScheduleDetail.objects.create(
            schedule=self.schedule,
            day_of_week=1,  # Tuesday
            frequency_duration=30
        )

        # Employee clocks in at 10:00
        arrival_timestamp = self.tuesday_date.replace(hour=10, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Employee clocks out at 10:20 (20 minutes later, which is insufficient)
        # With 10% tolerance, minimum duration should be 27 minutes
        departure_timestamp = self.tuesday_date.replace(hour=10, minute=20)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Call the scan_anomalies endpoint to detect anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['anomalies_created'], 0)

        # Verify anomaly is created for insufficient duration
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies.count(), 1)

        # Verify the anomaly details
        anomaly = anomalies.first()
        self.assertIn('Durée de présence insuffisante pour planning fréquence', anomaly.description)
        self.assertIn('Durée: 20 minutes', anomaly.description)
        self.assertIn('Minimum requis: 27 minutes', anomaly.description)

        # Verify that the schedule is associated with the anomaly
        self.assertEqual(anomaly.schedule, self.schedule)

        # Verify that the related timesheets are associated with the anomaly
        related_timesheets = anomaly.related_timesheets.all()
        self.assertEqual(related_timesheets.count(), 2)
        self.assertIn(arrival_timesheet, related_timesheets)
        self.assertIn(departure_timesheet, related_timesheets)

    def test_anomaly_with_schedule_and_timesheets(self):
        """Test that anomalies include the schedule and timesheets that triggered them."""
        # Set up a frequency schedule with 30 minutes duration
        from sites.models import ScheduleDetail
        ScheduleDetail.objects.filter(schedule=self.schedule).delete()

        # Create a new schedule detail with 30 minutes duration
        ScheduleDetail.objects.create(
            schedule=self.schedule,
            day_of_week=1,  # Tuesday
            frequency_duration=30
        )

        # Employee clocks in at 10:00
        arrival_timestamp = self.tuesday_date.replace(hour=10, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Call the scan_anomalies endpoint to detect anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify anomaly is created for missing departure
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Verify the anomaly details
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.schedule)

        # Verify that the related timesheets are associated with the anomaly
        related_timesheets = anomaly.related_timesheets.all()
        self.assertEqual(related_timesheets.count(), 1)
        self.assertIn(arrival_timesheet, related_timesheets)

        # Verify that the serializer includes the schedule and related timesheets
        from rest_framework.test import APIRequestFactory
        from timesheets.serializers import AnomalySerializer

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.manager

        serializer = AnomalySerializer(anomaly, context={'request': request})
        data = serializer.data

        self.assertIsNotNone(data['schedule_details'])
        self.assertEqual(data['schedule_details']['id'], self.schedule.id)
        self.assertEqual(data['schedule_details']['schedule_type'], self.schedule.schedule_type)

        self.assertIsNotNone(data['related_timesheets_details'])
        self.assertEqual(len(data['related_timesheets_details']), 1)
        self.assertEqual(data['related_timesheets_details'][0]['id'], arrival_timesheet.id)

    def test_single_clock(self):
        """Test Workflow 11: Single clock-in or clock-out."""
        # Employee clocks in at 10:00 (only one clock)
        arrival_timestamp = self.tuesday_date.replace(hour=10, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Appeler l'API pour détecter les anomalies automatiquement
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['anomalies_created'], 0)

        # Verify anomaly is created for missing departure
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_no_clocks(self):
        """Test Workflow 12: No clocks on scheduled day."""
        # Simuler end of day check
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.tuesday_date.replace(hour=23, minute=59)
            
            # Appeler l'API pour détecter les anomalies automatiquement
            client = APIClient()
            client.force_authenticate(user=self.manager)
            response = client.post(
                reverse('scan-anomalies'),
                {
                    'start_date': self.tuesday_date.date(),
                    'end_date': self.tuesday_date.date(),
                    'site': self.site.id,
                    'employee': self.employee.id
                },
                format='json'
            )
            
            # Vérifier la réponse
            self.assertEqual(response.status_code, 200)
            self.assertGreater(response.data['anomalies_created'], 0)

            # Verify anomaly is created for missing attendance
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.tuesday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

            # Verify alert is created
            alerts = Alert.objects.filter(
                employee=self.employee,
                site=self.site,
                anomaly=anomalies.first()
            )
            self.assertEqual(alerts.count(), 1)

    def test_multiple_clock_ins_frequency(self):
        """Test Workflow 17: Pointages multiples avec planning fréquence.
        
        Ce test vérifie que lorsqu'un employé effectue plusieurs pointages d'arrivée
        et de départ dans la même journée avec un planning fréquence, le système
        calcule correctement la durée totale de présence.
        """
        # Premier cycle de pointage
        # Arrivée à 9:00
        arrival_timestamp1 = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet1 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp1,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Départ à 10:30 (90 minutes plus tard)
        departure_timestamp1 = self.tuesday_date.replace(hour=10, minute=30)
        departure_timesheet1 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp1,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Deuxième cycle de pointage
        # Arrivée à 14:00
        arrival_timestamp2 = self.tuesday_date.replace(hour=14, minute=0)
        arrival_timesheet2 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp2,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Départ à 15:00 (60 minutes plus tard)
        departure_timestamp2 = self.tuesday_date.replace(hour=15, minute=0)
        departure_timesheet2 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp2,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Vérifier qu'aucune anomalie n'est créée (durée totale = 150 minutes > 90 minutes requises)
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies.count(), 0)
        
        # Vérifier aussi qu'il n'y a pas d'autres anomalies
        all_anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date()
        )
        self.assertEqual(all_anomalies.count(), 0)

    def test_insufficient_hours_multiple_passages(self):
        """Test pour vérifier que les durées cumulées des passages sont bien prises en compte.
        
        Ce test simule plusieurs passages courts qui, cumulés, restent insuffisants pour
        atteindre la durée minimale requise du planning fréquence.
        """
        # Premier passage: 30 minutes
        arrival_timestamp1 = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet1 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp1,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        departure_timestamp1 = self.tuesday_date.replace(hour=9, minute=30)
        departure_timesheet1 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp1,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Deuxième passage: 25 minutes
        arrival_timestamp2 = self.tuesday_date.replace(hour=14, minute=0)
        arrival_timesheet2 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp2,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        departure_timestamp2 = self.tuesday_date.replace(hour=14, minute=25)
        departure_timesheet2 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp2,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Total: 55 minutes (insuffisant pour le planning qui en requiert 90)
        
        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Vérifier qu'une anomalie d'heures insuffisantes est créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertIn("insuffisante", anomaly.description.lower())
        self.assertIn("55", anomaly.description)  # Durée totale: 55 minutes
        
        # Vérifier que l'alerte a été créée
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_out_of_schedule_day(self):
        """Test Workflow 15: Pointage hors planning (jour non configuré) avec planning fréquence."""
        # Configurer un jour où il n'y a pas de planning (mercredi)
        wednesday_date = self.tuesday_date + timedelta(days=1)
        
        # Arrivée un mercredi à 9:00
        arrival_timestamp = wednesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Départ à 10:30 (90 minutes plus tard)
        departure_timestamp = wednesday_date.replace(hour=10, minute=30)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': wednesday_date.date(),
                'end_date': wednesday_date.date(),
                'site': self.site.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Rafraîchir les données des timesheets depuis la base de données
        arrival_timesheet.refresh_from_db()
        departure_timesheet.refresh_from_db()
        
        # Vérifier qu'une anomalie est créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=wednesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertIn("hors planning", anomalies.first().description.lower())
        
        # Vérifier qu'une alerte a été créée
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_unassigned_schedule(self):
        """Test Workflow 16: Pointage sur un planning fréquence non rattaché au salarié."""
        # Créer un autre employé
        other_employee = User.objects.create_user(
            username='other_employee',
            email='other@test.com',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            first_name='Other',
            last_name='Employee'
        )
        other_employee.organizations.add(self.organization)
        
        # Associer cet employé au site mais pas au planning
        SiteEmployee.objects.create(
            site=self.site,
            employee=other_employee,
            is_active=True
        )
        
        # Pointage pour cet employé un mardi (jour où le planning fréquence existe)
        arrival_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=other_employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Départ à 10:30
        departure_timestamp = self.tuesday_date.replace(hour=10, minute=30)
        departure_timesheet = Timesheet.objects.create(
            employee=other_employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site.id,
                'employee': other_employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Rafraîchir les données des timesheets depuis la base de données
        arrival_timesheet.refresh_from_db()
        departure_timesheet.refresh_from_db()
        
        # Vérifier qu'une anomalie est créée
        anomalies = Anomaly.objects.filter(
            employee=other_employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertIn("planning", anomalies.first().description.lower())
        
        # Vérifier qu'une alerte a été créée
        alerts = Alert.objects.filter(
            employee=other_employee,
            site=self.site,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_unassigned_site(self):
        """Test pour le pointage sur un site non rattaché avec planning fréquence."""
        # L'employé fait un pointage sur le site2 auquel il n'est pas associé
        arrival_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site2,  # Site non associé à l'employé
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Départ
        departure_timestamp = self.tuesday_date.replace(hour=10, minute=30)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site2,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site2.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Rafraîchir les données des timesheets depuis la base de données
        arrival_timesheet.refresh_from_db()
        departure_timesheet.refresh_from_db()
        
        # Vérifier qu'une anomalie est créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site2,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertIn("site", anomalies.first().description.lower())
        
        # Vérifier qu'une alerte a été créée
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site2,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_other_organization_site_clock_in_frequency(self):
        """Test pour le pointage sur un site d'une autre organisation avec planning fréquence."""
        # Pointage sur un site d'une autre organisation
        arrival_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site3,  # Site d'une autre organisation
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Départ
        departure_timestamp = self.tuesday_date.replace(hour=10, minute=30)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site3,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': self.site3.id,
                'employee': self.employee.id
            },
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Rafraîchir les données des timesheets depuis la base de données
        arrival_timesheet.refresh_from_db()
        departure_timesheet.refresh_from_db()
        
        # Vérifier qu'une anomalie est créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site3,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertIn("organisation", anomalies.first().description.lower())
        
        # Vérifier qu'une alerte a été créée
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site3,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_tolerance_edge_cases(self):
        """Test pour les cas limites de la tolérance de fréquence."""
        # Configurer un site avec tolérance de fréquence de 10%
        site_with_tolerance = Site.objects.create(
            name='Tolerance Test Site',
            address='123 Tolerance St',
            postal_code='75000',
            city='Paris',
            organization=self.organization,
            nfc_id='TOL-001',
            frequency_tolerance=10
        )

        # Créer un planning fréquence de 90 minutes
        tolerance_schedule = Schedule.objects.create(
            site=site_with_tolerance,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )

        # Mardi avec durée requise de 90 minutes
        ScheduleDetail.objects.create(
            schedule=tolerance_schedule,
            day_of_week=1,  # Mardi
            frequency_duration=90
        )

        # Associer l'employé au site et au planning
        SiteEmployee.objects.create(
            site=site_with_tolerance,
            employee=self.employee,
            schedule=tolerance_schedule,
            is_active=True
        )

        # Cas limite 1: Passage exactement à la limite de la tolérance (81 minutes = 90 - 10%)
        # Arrivée à 10:00
        arrival_timestamp1 = self.tuesday_date.replace(hour=10, minute=0)
        arrival_timesheet1 = Timesheet.objects.create(
            employee=self.employee,
            site=site_with_tolerance,
            timestamp=arrival_timestamp1,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Départ à 11:21 (81 minutes plus tard)
        departure_timestamp1 = self.tuesday_date.replace(hour=11, minute=21)
        departure_timesheet1 = Timesheet.objects.create(
            employee=self.employee,
            site=site_with_tolerance,
            timestamp=departure_timestamp1,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Appeler l'API pour détecter les anomalies
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': site_with_tolerance.id,
                'employee': self.employee.id
            },
            format='json'
        )

        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)

        # Vérifier qu'aucune anomalie n'est créée (durée exactement à la limite de tolérance)
        anomalies1 = Anomaly.objects.filter(
            employee=self.employee,
            site=site_with_tolerance,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies1.count(), 0)

        # Supprimer les timesheets pour le prochain test
        Timesheet.objects.all().delete()

        # Cas limite 2: Passage juste en dessous de la limite de tolérance (80 minutes)
        # Arrivée à 14:00
        arrival_timestamp2 = self.tuesday_date.replace(hour=14, minute=0)
        arrival_timesheet2 = Timesheet.objects.create(
            employee=self.employee,
            site=site_with_tolerance,
            timestamp=arrival_timestamp2,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Départ à 15:20 (80 minutes plus tard)
        departure_timestamp2 = self.tuesday_date.replace(hour=15, minute=20)
        departure_timesheet2 = Timesheet.objects.create(
            employee=self.employee,
            site=site_with_tolerance,
            timestamp=departure_timestamp2,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Appeler l'API pour détecter les anomalies
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': self.tuesday_date.date(),
                'end_date': self.tuesday_date.date(),
                'site': site_with_tolerance.id,
                'employee': self.employee.id
            },
            format='json'
        )

        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)

        # Vérifier qu'une anomalie est créée (durée insuffisante)
        anomalies2 = Anomaly.objects.filter(
            employee=self.employee,
            site=site_with_tolerance,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies2.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = anomalies2.first()
        self.assertIn("80 minutes", anomaly.description)
        self.assertIn("81 minutes", anomaly.description)  # Minimum requis
        
        # Vérifier qu'une alerte est créée
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=site_with_tolerance,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)
