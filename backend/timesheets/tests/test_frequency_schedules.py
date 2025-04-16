"""
Tests pour vérifier la détection d'anomalies pour les plannings de type fréquence
"""
from datetime import datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization
from timesheets.utils.anomaly_processor import AnomalyProcessor

User = get_user_model()

class FrequencyScheduleTestCase(TestCase):
    """Tests pour la détection d'anomalies pour les plannings de type fréquence"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer une organisation
        self.organization = Organization.objects.create(
            name="Test Organization",
            address="123 Test Street",
            postal_code="12345",
            city="Test City",
            country="France",
            siret="12345678901234"
        )

        # Créer un site
        self.site = Site.objects.create(
            name="Test Site",
            address="123 Test Street",
            postal_code="12345",
            city="Test City",
            country="France",
            organization=self.organization,
            nfc_id="TST-S0001",
            frequency_tolerance=10  # 10% de tolérance
        )

        # Créer un employé
        self.employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="password",
            first_name="Test",
            last_name="Employee",
            role="EMPLOYEE"
        )

        # Créer un planning fréquence
        self.frequency_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            frequency_tolerance_percentage=10,  # 10% de tolérance
            is_active=True
        )

        # Associer l'employé au site avec le planning fréquence
        self.site_employee = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.frequency_schedule,
            is_active=True
        )

        # Créer les détails du planning fréquence pour aujourd'hui
        today_weekday = timezone.now().weekday()
        self.schedule_detail = ScheduleDetail.objects.create(
            schedule=self.frequency_schedule,
            day_of_week=today_weekday,
            frequency_duration=240  # 4 heures (240 minutes)
        )

        # Initialiser le processeur d'anomalies
        self.anomaly_processor = AnomalyProcessor()

    def test_frequency_sufficient_duration(self):
        """Test qu'aucune anomalie n'est créée si la durée est suffisante"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ après la durée attendue
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),  # 12h00 (4 heures après l'arrivée)
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)

    def test_frequency_within_tolerance(self):
        """Test qu'aucune anomalie n'est créée si la durée est dans la marge de tolérance"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ légèrement avant la durée attendue mais dans la tolérance
        # 240 minutes - 10% = 216 minutes minimum
        # 8h00 + 3h36 = 11h36
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=11, minute=36),  # 11h36 (3h36 après l'arrivée)
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)

    def test_frequency_insufficient_duration(self):
        """Test qu'une anomalie est créée si la durée est insuffisante"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ bien avant la durée attendue
        # 240 minutes - 10% = 216 minutes minimum
        # 8h00 + 3h00 = 11h00 (insuffisant)
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=11, minute=0),  # 11h00 (3h00 après l'arrivée)
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.EARLY_DEPARTURE)
        self.assertEqual(anomaly.employee, self.employee)
        self.assertEqual(anomaly.site, self.site)
        self.assertIn("Durée insuffisante", anomaly.description)
        self.assertIn("180.0 minutes", anomaly.description)  # 3h00 = 180 minutes
        self.assertIn("216.0 minutes minimum", anomaly.description)  # 240 - 10% = 216 minutes

    def test_frequency_missing_arrival(self):
        """Test qu'une anomalie est créée pour un pointage d'arrivée manquant"""
        # Vérifier les absences pour aujourd'hui
        today = timezone.now().date()
        absences = self.anomaly_processor.check_employee_absences(today, today)

        # Vérifier qu'une anomalie a été créée
        self.assertEqual(absences, 1)
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.MISSING_ARRIVAL)
        self.assertEqual(anomaly.employee, self.employee)
        self.assertEqual(anomaly.site, self.site)
        self.assertIn("Pointage manquant selon le planning fréquence", anomaly.description)
        self.assertIn("240 minutes", anomaly.description)

    def test_frequency_update_missing_arrival_to_insufficient_hours(self):
        """Test qu'une anomalie d'arrivée manquante est mise à jour si l'employé pointe avec une durée insuffisante"""
        # Créer une anomalie d'arrivée manquante
        missing_arrival = Anomaly.objects.create(
            employee=self.employee,
            site=self.site,
            date=timezone.now().date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
            description="Pointage manquant selon le planning fréquence (durée prévue: 240 minutes)",
            status=Anomaly.AnomalyStatus.PENDING,
            schedule=self.frequency_schedule
        )

        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ avec une durée insuffisante
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=11, minute=0),  # 11h00 (3h00 après l'arrivée)
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée/mise à jour
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)  # Toujours une seule anomalie

        # Vérifier les détails de l'anomalie
        updated_anomaly = Anomaly.objects.first()
        self.assertEqual(updated_anomaly.anomaly_type, Anomaly.AnomalyType.EARLY_DEPARTURE)
        self.assertIn("Durée insuffisante", updated_anomaly.description)

    def test_frequency_different_tolerance(self):
        """Test que la tolérance spécifique au planning est utilisée"""
        # Modifier la tolérance du planning
        self.frequency_schedule.frequency_tolerance_percentage = 20  # 20% de tolérance
        self.frequency_schedule.save()

        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ avec une durée qui serait insuffisante avec 10% mais acceptable avec 20%
        # 240 minutes - 20% = 192 minutes minimum
        # 8h00 + 3h12 = 11h12
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=11, minute=12),  # 11h12 (3h12 après l'arrivée)
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'aucune anomalie n'a été créée (car dans la tolérance de 20%)
        self.assertFalse(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)
