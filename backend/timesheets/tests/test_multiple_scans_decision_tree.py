"""
Tests pour vérifier que la détection des scans multiples suit parfaitement l'arbre de décision
défini dans .cursor/rules/scan_anomalies.mdc
"""
import logging
from datetime import datetime, time, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization
from timesheets.utils.anomaly_processor import AnomalyProcessor

User = get_user_model()

# Configurer le logging pour les tests
logging.basicConfig(level=logging.DEBUG)

@override_settings(DEBUG=True)
class MultipleScansDecisionTreeTestCase(TestCase):
    """Tests pour vérifier que la détection des scans multiples suit parfaitement l'arbre de décision"""

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

        # Créer des employés pour chaque type de planning
        self.employee_full_day = User.objects.create_user(
            username="employee_full_day",
            email="employee_full_day@example.com",
            password="password",
            first_name="Full",
            last_name="Day",
            role="EMPLOYEE"
        )

        self.employee_morning = User.objects.create_user(
            username="employee_morning",
            email="employee_morning@example.com",
            password="password",
            first_name="Morning",
            last_name="Only",
            role="EMPLOYEE"
        )

        self.employee_afternoon = User.objects.create_user(
            username="employee_afternoon",
            email="employee_afternoon@example.com",
            password="password",
            first_name="Afternoon",
            last_name="Only",
            role="EMPLOYEE"
        )

        self.employee_frequency = User.objects.create_user(
            username="employee_frequency",
            email="employee_frequency@example.com",
            password="password",
            first_name="Frequency",
            last_name="Based",
            role="EMPLOYEE"
        )

        # Créer les plannings
        self.full_day_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        self.morning_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        self.afternoon_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            late_arrival_margin=15,
            early_departure_margin=15,
            is_active=True
        )

        self.frequency_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            frequency_tolerance_percentage=10,
            is_active=True
        )

        # Associer les employés aux plannings
        self.site_employee_full_day = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee_full_day,
            schedule=self.full_day_schedule,
            is_active=True
        )

        self.site_employee_morning = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee_morning,
            schedule=self.morning_schedule,
            is_active=True
        )

        self.site_employee_afternoon = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee_afternoon,
            schedule=self.afternoon_schedule,
            is_active=True
        )

        self.site_employee_frequency = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee_frequency,
            schedule=self.frequency_schedule,
            is_active=True
        )

        # Créer les détails des plannings pour aujourd'hui
        self.today = timezone.now().date()
        self.today_weekday = self.today.weekday()

        # Planning journée complète
        self.schedule_detail_full_day = ScheduleDetail.objects.create(
            schedule=self.full_day_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.FULL,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Planning demi-journée matin
        self.schedule_detail_morning = ScheduleDetail.objects.create(
            schedule=self.morning_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.AM,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0)    # 12h00
        )

        # Planning demi-journée après-midi
        self.schedule_detail_afternoon = ScheduleDetail.objects.create(
            schedule=self.afternoon_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.PM,
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Planning fréquence
        self.schedule_detail_frequency = ScheduleDetail.objects.create(
            schedule=self.frequency_schedule,
            day_of_week=self.today_weekday,
            frequency_duration=240  # 4 heures
        )

        # Initialiser le processeur d'anomalies
        self.anomaly_processor = AnomalyProcessor()

    def test_full_day_multiple_scans(self):
        """
        Test pour un planning journée complète avec plus de 4 pointages
        Arbre de décision: Planning fixe -> Journée complète -> Plus de 4 pointages -> Anomalie scan multiple
        """
        # Créer 4 pointages normaux
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        
        # Créer un 5ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=18, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.full_day_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("journée complète", anomaly.description)
        
        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 5)

    def test_morning_schedule_multiple_scans(self):
        """
        Test pour un planning demi-journée matin avec plus de 2 pointages
        Arbre de décision: Planning fixe -> Demi-journée matin -> Plus de 2 pointages -> Anomalie scan multiple
        """
        # Créer 2 pointages normaux
        Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        
        # Créer un 3ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.morning_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("demi-journée matin", anomaly.description)
        
        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_afternoon_schedule_multiple_scans(self):
        """
        Test pour un planning demi-journée après-midi avec plus de 2 pointages
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Plus de 2 pointages -> Anomalie scan multiple
        """
        # Créer 2 pointages normaux
        Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        
        # Créer un 3ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=timezone.now().replace(hour=18, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.afternoon_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("demi-journée après-midi", anomaly.description)
        
        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_frequency_schedule_multiple_scans(self):
        """
        Test pour un planning fréquence avec plus de 2 pointages
        Arbre de décision: Planning fréquence -> Plus de 2 pointages -> Anomalie scan multiple
        """
        # Créer 2 pointages normaux
        Timesheet.objects.create(
            employee=self.employee_frequency,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_frequency,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        
        # Créer un 3ème pointage (scan multiple)
        timesheet = Timesheet.objects.create(
            employee=self.employee_frequency,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_frequency,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.frequency_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("fréquence", anomaly.description)
        
        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_update_existing_multiple_scan_anomaly(self):
        """
        Test pour la mise à jour d'une anomalie de scan multiple existante
        Arbre de décision: Planning fixe -> Journée complète -> Plus de 4 pointages -> Anomalie existante -> Mise à jour
        """
        # Créer 5 pointages (4 normaux + 1 scan multiple)
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        timesheet1 = Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=18, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le premier pointage supplémentaire
        result1 = self.anomaly_processor.process_timesheet(timesheet1)
        
        # Vérifier qu'une anomalie a été créée
        anomalies_after_first = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies_after_first.count(), 1)
        first_anomaly = anomalies_after_first.first()
        self.assertEqual(first_anomaly.related_timesheets.count(), 5)
        
        # Créer un 6ème pointage (scan multiple supplémentaire)
        timesheet2 = Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=19, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        
        # Traiter le deuxième pointage supplémentaire
        result2 = self.anomaly_processor.process_timesheet(timesheet2)
        
        # Vérifier que l'anomalie existante a été mise à jour
        anomalies_after_second = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies_after_second.count(), 1)  # Toujours une seule anomalie
        updated_anomaly = anomalies_after_second.first()
        self.assertEqual(updated_anomaly.id, first_anomaly.id)  # Même ID = même anomalie
        self.assertEqual(updated_anomaly.related_timesheets.count(), 6)  # Maintenant 6 pointages associés

    def test_no_anomaly_for_expected_scans(self):
        """
        Test pour le nombre attendu de pointages (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Journée complète -> 4 pointages ou moins -> Pas d'anomalie
        """
        # Créer 4 pointages (exactement le nombre attendu pour une journée complète)
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        timesheet = Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        
        # Traiter le dernier pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 0)

    def test_no_schedule_no_anomaly(self):
        """
        Test pour un employé sans planning (aucune anomalie de scan multiple ne doit être créée)
        Arbre de décision: Pas de planning -> Pas d'anomalie de scan multiple
        """
        # Supprimer l'association entre l'employé et le planning
        self.site_employee_full_day.schedule = None
        self.site_employee_full_day.save()
        
        # Créer 5 pointages (plus que le nombre attendu)
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        timesheet = Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=18, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'aucune anomalie de scan multiple n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 0)
        
        # Restaurer l'association
        self.site_employee_full_day.schedule = self.full_day_schedule
        self.site_employee_full_day.save()

    def test_no_schedule_detail_no_anomaly(self):
        """
        Test pour un jour sans détail de planning (aucune anomalie de scan multiple ne doit être créée)
        Arbre de décision: Planning actif -> Pas de détail pour ce jour -> Pas d'anomalie de scan multiple
        """
        # Supprimer les détails du planning pour aujourd'hui
        ScheduleDetail.objects.filter(
            schedule=self.full_day_schedule,
            day_of_week=self.today_weekday
        ).delete()
        
        # Créer 5 pointages (plus que le nombre attendu)
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=13, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=17, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )
        timesheet = Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=18, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Traiter le pointage
        result = self.anomaly_processor.process_timesheet(timesheet)
        
        # Vérifier qu'aucune anomalie de scan multiple n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies.count(), 0)
        
        # Recréer les détails du planning
        ScheduleDetail.objects.create(
            schedule=self.full_day_schedule,
            day_of_week=self.today_weekday,
            day_type=ScheduleDetail.DayType.FULL,
            start_time_1=time(8, 0),
            end_time_1=time(12, 0),
            start_time_2=time(13, 0),
            end_time_2=time(17, 0)
        )
