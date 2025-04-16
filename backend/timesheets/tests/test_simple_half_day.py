"""
Test simple pour vérifier la détection d'anomalies pour les plannings demi-journée
"""
import logging
from datetime import datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization
from timesheets.utils.anomaly_processor import AnomalyProcessor

User = get_user_model()

class SimpleHalfDayTestCase(TestCase):
    """Test simple pour vérifier la détection d'anomalies pour les plannings demi-journée"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        # Configurer le logger
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
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

        # Associer l'employé au site avec le planning demi-journée matin
        self.site_employee = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.am_schedule,
            is_active=True
        )

        # Créer les détails du planning demi-journée matin pour aujourd'hui
        self.today = timezone.now().date()
        self.today_weekday = self.today.weekday()
        self.schedule_detail = ScheduleDetail.objects.create(
            schedule=self.am_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.AM,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0)    # 12h00
        )

        # Initialiser le processeur d'anomalies
        self.anomaly_processor = AnomalyProcessor()

    def test_late_arrival(self):
        """Test qu'une anomalie de retard est créée pour un planning demi-journée matin"""
        # Créer un pointage d'arrivée en retard
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=30).replace(second=0, microsecond=0),  # 8h30 (30 minutes de retard)
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Afficher les détails du pointage
        self.logger.debug(f"Pointage créé: {timesheet.employee.get_full_name()} - {timesheet.site.name} - {timesheet.timestamp} - {timesheet.entry_type}")
        
        # Afficher les détails du planning
        self.logger.debug(f"Planning: {self.am_schedule.schedule_type} - {self.schedule_detail.day_type} - {self.schedule_detail.start_time_1} - {self.schedule_detail.end_time_1}")
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Afficher le résultat
        self.logger.debug(f"Résultat: {result}")
        
        # Vérifier qu'une anomalie a été créée
        self.assertTrue(result['has_anomalies'])
        self.assertEqual(Anomaly.objects.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = Anomaly.objects.first()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.LATE)
        self.assertEqual(anomaly.employee, self.employee)
        self.assertEqual(anomaly.site, self.site)
        self.assertEqual(anomaly.minutes, 30)
        self.assertIn("matin", anomaly.description)
        
        # Afficher les détails de l'anomalie
        self.logger.debug(f"Anomalie créée: {anomaly.anomaly_type} - {anomaly.description} - {anomaly.minutes} minutes")
