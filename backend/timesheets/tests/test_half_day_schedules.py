"""
Tests pour vérifier la gestion des plannings demi-journée
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

class HalfDayScheduleTestCase(TestCase):
    """Tests pour la gestion des plannings demi-journée"""

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

        # Créer un planning fixe pour demi-journée matin
        self.am_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        # Créer un planning fixe pour demi-journée après-midi
        self.pm_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        # Associer l'employé au site avec le planning demi-journée matin
        self.site_employee_am = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.am_schedule,
            is_active=True
        )

        # Créer un autre employé pour le planning demi-journée après-midi
        self.employee2 = User.objects.create_user(
            username="employee2",
            email="employee2@example.com",
            password="password",
            first_name="Test2",
            last_name="Employee2",
            role="EMPLOYEE"
        )

        # Associer le deuxième employé au site avec le planning demi-journée après-midi
        self.site_employee_pm = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee2,
            schedule=self.pm_schedule,
            is_active=True
        )

        # Créer les détails du planning demi-journée matin pour aujourd'hui
        self.today = timezone.now().date()
        self.today_weekday = self.today.weekday()
        self.schedule_detail_am = ScheduleDetail.objects.create(
            schedule=self.am_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.AM,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0)    # 12h00
        )

        # Créer les détails du planning demi-journée après-midi pour aujourd'hui
        self.schedule_detail_pm = ScheduleDetail.objects.create(
            schedule=self.pm_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.PM,
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)     # 17h00
        )

        # Initialiser le processeur d'anomalies
        self.anomaly_processor = AnomalyProcessor()

    def test_am_schedule_late_arrival(self):
        """Test qu'une anomalie de retard est créée pour un planning demi-journée matin"""
        # Créer un pointage d'arrivée en retard
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=30).replace(second=0, microsecond=0),  # 8h30 (30 minutes de retard)
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.LATE)
        self.assertEqual(anomaly.employee, self.employee)
        self.assertEqual(anomaly.site, self.site)
        self.assertEqual(anomaly.minutes, 30)
        self.assertIn("Planning demi-journée matin", anomaly.description)
        self.assertIn("matin", anomaly.description)

    def test_pm_schedule_late_arrival(self):
        """Test qu'une anomalie de retard est créée pour un planning demi-journée après-midi"""
        # Créer un pointage d'arrivée en retard
        timesheet = Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=30).replace(second=0, microsecond=0),  # 13h30 (30 minutes de retard)
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.LATE)
        self.assertEqual(anomaly.employee, self.employee2)
        self.assertEqual(anomaly.site, self.site)
        self.assertEqual(anomaly.minutes, 30)
        self.assertIn("Planning demi-journée après-midi", anomaly.description)
        self.assertIn("après-midi", anomaly.description)

    def test_am_schedule_early_departure(self):
        """Test qu'une anomalie de départ anticipé est créée pour un planning demi-journée matin"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ anticipé
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=11, minute=30).replace(second=0, microsecond=0),  # 11h30 (30 minutes avant la fin)
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
        self.assertEqual(anomaly.minutes, 30)
        self.assertIn("Planning demi-journée matin", anomaly.description)
        self.assertIn("matin", anomaly.description)

    def test_pm_schedule_early_departure(self):
        """Test qu'une anomalie de départ anticipé est créée pour un planning demi-journée après-midi"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ anticipé
        timesheet = Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=16, minute=30).replace(second=0, microsecond=0),  # 16h30 (30 minutes avant la fin)
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
        self.assertEqual(anomaly.employee, self.employee2)
        self.assertEqual(anomaly.site, self.site)
        self.assertEqual(anomaly.minutes, 30)
        self.assertIn("Planning demi-journée après-midi", anomaly.description)
        self.assertIn("après-midi", anomaly.description)

    def test_am_schedule_no_anomaly_on_time(self):
        """Test qu'aucune anomalie n'est créée pour un pointage à l'heure en demi-journée matin"""
        # Créer un pointage d'arrivée à l'heure
        timesheet_arrival = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),  # 8h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage d'arrivée
        result_arrival = self.anomaly_processor.process_timesheet(timesheet_arrival)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result_arrival['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)

        # Créer un pointage de départ à l'heure
        timesheet_departure = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),  # 12h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage de départ
        result_departure = self.anomaly_processor.process_timesheet(timesheet_departure)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result_departure['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)

    def test_pm_schedule_no_anomaly_on_time(self):
        """Test qu'aucune anomalie n'est créée pour un pointage à l'heure en demi-journée après-midi"""
        # Créer un pointage d'arrivée à l'heure
        timesheet_arrival = Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage d'arrivée
        result_arrival = self.anomaly_processor.process_timesheet(timesheet_arrival)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result_arrival['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)

        # Créer un pointage de départ à l'heure
        timesheet_departure = Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),  # 17h00
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage de départ
        result_departure = self.anomaly_processor.process_timesheet(timesheet_departure)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertFalse(result_departure['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 0)

    def test_am_schedule_update_missing_arrival_to_late(self):
        """Test qu'une anomalie d'arrivée manquante est mise à jour en retard pour un planning demi-journée matin"""
        # Créer une anomalie d'arrivée manquante
        missing_arrival = Anomaly.objects.create(
            employee=self.employee,
            site=self.site,
            date=timezone.now().date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
            description="Arrivée manquante selon le planning",
            status=Anomaly.AnomalyStatus.PENDING,
            schedule=self.am_schedule
        )

        # Créer un pointage d'arrivée en retard
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=30).replace(second=0, microsecond=0),  # 8h30 (30 minutes de retard)
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier que l'anomalie a été mise à jour
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie mise à jour
        updated_anomaly = Anomaly.objects.first()
        self.assertEqual(updated_anomaly.id, missing_arrival.id)  # Même ID = même anomalie
        self.assertEqual(updated_anomaly.anomaly_type, Anomaly.AnomalyType.LATE)
        self.assertEqual(updated_anomaly.minutes, 30)
        self.assertIn("Planning demi-journée matin", updated_anomaly.description)
        self.assertIn("matin", updated_anomaly.description)

    def test_pm_schedule_update_missing_departure_to_early_departure(self):
        """Test qu'une anomalie de départ manquant est mise à jour en départ anticipé pour un planning demi-journée après-midi"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),  # 13h00
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer une anomalie de départ manquant
        missing_departure = Anomaly.objects.create(
            employee=self.employee2,
            site=self.site,
            date=timezone.now().date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
            description="Départ manquant selon le planning",
            status=Anomaly.AnomalyStatus.PENDING,
            schedule=self.pm_schedule
        )

        # Créer un pointage de départ anticipé
        timesheet = Timesheet.objects.create(
            employee=self.employee2,
            site=self.site,
            timestamp=timezone.now().replace(hour=16, minute=30).replace(second=0, microsecond=0),  # 16h30 (30 minutes avant la fin)
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier que l'anomalie a été mise à jour
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)

        # Vérifier les détails de l'anomalie mise à jour
        updated_anomaly = Anomaly.objects.first()
        self.assertEqual(updated_anomaly.id, missing_departure.id)  # Même ID = même anomalie
        self.assertEqual(updated_anomaly.anomaly_type, Anomaly.AnomalyType.EARLY_DEPARTURE)
        self.assertEqual(updated_anomaly.minutes, 30)
        self.assertIn("Planning demi-journée après-midi", updated_anomaly.description)
        self.assertIn("après-midi", updated_anomaly.description)
