"""
Tests pour vérifier la détection des scans multiples
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

class MultipleScansTestCase(TestCase):
    """Tests pour la détection des scans multiples"""

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
            late_margin=15,
            early_departure_margin=15
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

        # Créer un planning fixe journée complète
        self.full_day_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        # Créer un planning fixe demi-journée
        self.half_day_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        # Créer un planning fréquence
        self.frequency_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            frequency_tolerance_percentage=10,
            is_active=True
        )

        # Associer l'employé au site avec le planning journée complète
        self.site_employee_full = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.full_day_schedule,
            is_active=True
        )

        # Créer un autre employé pour le planning demi-journée
        self.employee2 = User.objects.create_user(
            username="employee2",
            email="employee2@example.com",
            password="password",
            first_name="Test2",
            last_name="Employee2",
            role="EMPLOYEE"
        )

        # Associer le deuxième employé au site avec le planning demi-journée
        self.site_employee_half = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee2,
            schedule=self.half_day_schedule,
            is_active=True
        )

        # Créer un troisième employé pour le planning fréquence
        self.employee3 = User.objects.create_user(
            username="employee3",
            email="employee3@example.com",
            password="password",
            first_name="Test3",
            last_name="Employee3",
            role="EMPLOYEE"
        )

        # Associer le troisième employé au site avec le planning fréquence
        self.site_employee_frequency = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee3,
            schedule=self.frequency_schedule,
            is_active=True
        )

        # Créer les détails du planning journée complète pour aujourd'hui
        today_weekday = timezone.now().weekday()
        self.schedule_detail_full = ScheduleDetail.objects.create(
            schedule=self.full_day_schedule,
            day_of_week=today_weekday,
            day_type=ScheduleDetail.DayType.FULL,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Créer les détails du planning demi-journée pour aujourd'hui
        self.schedule_detail_half = ScheduleDetail.objects.create(
            schedule=self.half_day_schedule,
            day_of_week=today_weekday,
            day_type=ScheduleDetail.DayType.AM,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0)    # 12h00
        )

        # Créer les détails du planning fréquence pour aujourd'hui
        self.schedule_detail_frequency = ScheduleDetail.objects.create(
            schedule=self.frequency_schedule,
            day_of_week=today_weekday,
            frequency_duration=240  # 4 heures
        )

        # Initialiser le processeur d'anomalies
        self.anomaly_processor = AnomalyProcessor()

    def test_full_day_multiple_scans(self):
        """Test qu'une anomalie est créée pour des scans multiples en journée complète"""
        # Créer 5 pointages (plus que les 4 attendus)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),  # 12h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0),  # 17h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Créer un 5ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=18, minute=0),  # 18h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE)
        self.assertEqual(anomaly.employee, self.employee)
        self.assertEqual(anomaly.site, self.site)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("journée complète", anomaly.description)
        self.assertIn("3 arrivée(s) et 2 départ(s)", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 5)

    def test_half_day_multiple_scans(self):
        """Test qu'une anomalie est créée pour des scans multiples en demi-journée"""
        # Créer 2 pointages (les 2 attendus)
        Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),  # 12h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Créer un 3ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE)
        self.assertEqual(anomaly.employee, self.employee2)
        self.assertEqual(anomaly.site, self.site)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("demi-journée matin", anomaly.description)
        self.assertIn("2 arrivée(s) et 1 départ(s)", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_frequency_multiple_scans(self):
        """Test qu'une anomalie est créée pour des scans multiples en planning fréquence"""
        # Créer 2 pointages (les 2 attendus)
        Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),  # 12h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Créer un 3ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE)
        self.assertEqual(anomaly.employee, self.employee3)
        self.assertEqual(anomaly.site, self.site)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("fréquence", anomaly.description)
        self.assertIn("2 arrivée(s) et 1 départ(s)", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_update_existing_multiple_scan_anomaly(self):
        """Test qu'une anomalie existante de scan multiple est mise à jour"""
        # Créer 3 pointages (plus que les 2 attendus pour un planning fréquence)
        Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),  # 12h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Créer un 3ème pointage (scan multiple)
        timesheet1 = Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result1 = self.anomaly_processor.process_timesheet(timesheet1)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result1['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Créer un 4ème pointage (scan multiple supplémentaire)
        timesheet2 = Timesheet.objects.create(
            employee=self.employee3,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0),  # 17h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result2 = self.anomaly_processor.process_timesheet(timesheet2)

        # Vérifier que l'anomalie existante a été mise à jour
        self.assertTrue(result2['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)  # Toujours une seule anomalie

        # Vérifier les détails de l'anomalie mise à jour
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.related_timesheets.count(), 4)  # Maintenant 4 pointages associés

    def test_no_anomaly_for_expected_scans(self):
        """Test qu'aucune anomalie n'est créée pour le nombre attendu de pointages"""
        # Créer 4 pointages (exactement les 4 attendus pour une journée complète)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),  # 12h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0),  # 17h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le dernier pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)
