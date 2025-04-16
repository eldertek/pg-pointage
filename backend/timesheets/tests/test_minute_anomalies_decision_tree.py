"""
Tests pour vérifier que la détection d'anomalies par minute suit parfaitement l'arbre de décision
défini dans .cursor/rules/minute_anomalies.mdc
"""
import logging
from datetime import datetime, time, timedelta
from io import StringIO
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization
from timesheets.management.commands.check_minute_anomalies import Command

User = get_user_model()

# Configurer le logging pour les tests
logging.basicConfig(level=logging.DEBUG)

@override_settings(DEBUG=True)
class MinuteAnomaliesDecisionTreeTestCase(TestCase):
    """Tests pour vérifier que la détection d'anomalies par minute suit parfaitement l'arbre de décision"""

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

        # Créer l'instance de la commande pour les tests
        self.command = Command()

    def test_full_day_no_checkin_morning(self):
        """
        Test pour un planning journée complète sans pointage le matin
        Arbre de décision: Planning fixe -> Journée complète -> 0 pointage -> Heure actuelle > Heure arrivée matin + marge
        """
        # Définir l'heure actuelle à 8h30 (après l'heure de début + marge)
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'une anomalie a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today,
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)
            
            # Vérifier les détails de l'anomalie
            anomaly = anomalies.first()
            self.assertEqual(anomaly.schedule, self.full_day_schedule)
            self.assertIn("Pointage d'arrivée manquant", anomaly.description)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_full_day_morning_checkin_no_afternoon(self):
        """
        Test pour un planning journée complète avec pointage le matin mais pas l'après-midi
        Arbre de décision: Planning fixe -> Journée complète -> 2 pointages -> Heure actuelle > Heure arrivée après-midi + marge
        """
        # Créer les pointages du matin
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
        
        # Définir l'heure actuelle à 13h30 (après l'heure de début de l'après-midi + marge)
        current_time = datetime.combine(self.today, time(13, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'une anomalie a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today,
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)
            
            # Vérifier les détails de l'anomalie
            anomaly = anomalies.first()
            self.assertEqual(anomaly.schedule, self.full_day_schedule)
            self.assertIn("Pointage d'arrivée manquant", anomaly.description)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_morning_schedule_no_checkin(self):
        """
        Test pour un planning demi-journée matin sans pointage
        Arbre de décision: Planning fixe -> Demi-journée matin -> 0 pointage -> Heure actuelle > Heure arrivée + marge
        """
        # Définir l'heure actuelle à 8h30 (après l'heure de début + marge)
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_morning.id), stdout=out)
            
            # Vérifier qu'une anomalie a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_morning,
                site=self.site,
                date=self.today,
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)
            
            # Vérifier les détails de l'anomalie
            anomaly = anomalies.first()
            self.assertEqual(anomaly.schedule, self.morning_schedule)
            self.assertIn("Pointage d'arrivée manquant", anomaly.description)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_afternoon_schedule_no_checkin(self):
        """
        Test pour un planning demi-journée après-midi sans pointage
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> 0 pointage -> Heure actuelle > Heure arrivée + marge
        """
        # Définir l'heure actuelle à 13h30 (après l'heure de début + marge)
        current_time = datetime.combine(self.today, time(13, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_afternoon.id), stdout=out)
            
            # Vérifier qu'une anomalie a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_afternoon,
                site=self.site,
                date=self.today,
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)
            
            # Vérifier les détails de l'anomalie
            anomaly = anomalies.first()
            self.assertEqual(anomaly.schedule, self.afternoon_schedule)
            self.assertIn("Pointage d'arrivée manquant", anomaly.description)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_frequency_schedule_no_anomaly(self):
        """
        Test pour un planning fréquence (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fréquence -> Pas d'anomalie
        """
        # Définir l'heure actuelle à 8h30
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_frequency.id), stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_frequency,
                site=self.site,
                date=self.today
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_full_day_with_checkin_no_anomaly(self):
        """
        Test pour un planning journée complète avec pointage à l'heure (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Journée complète -> Pointage à l'heure -> Pas d'anomalie
        """
        # Créer un pointage d'arrivée à l'heure
        Timesheet.objects.create(
            employee=self.employee_full_day,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0).replace(second=0, microsecond=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        
        # Définir l'heure actuelle à 8h30
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today,
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_inactive_site_no_anomaly(self):
        """
        Test pour un site inactif (aucune anomalie ne doit être créée)
        Arbre de décision: Site inactif -> Pas d'anomalie
        """
        # Désactiver le site
        self.site.is_active = False
        self.site.save()
        
        # Définir l'heure actuelle à 8h30
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now
            # Réactiver le site
            self.site.is_active = True
            self.site.save()

    def test_inactive_schedule_no_anomaly(self):
        """
        Test pour un planning inactif (aucune anomalie ne doit être créée)
        Arbre de décision: Planning inactif -> Pas d'anomalie
        """
        # Désactiver le planning
        self.full_day_schedule.is_active = False
        self.full_day_schedule.save()
        
        # Définir l'heure actuelle à 8h30
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now
            # Réactiver le planning
            self.full_day_schedule.is_active = True
            self.full_day_schedule.save()

    def test_before_start_time_no_anomaly(self):
        """
        Test avant l'heure de début + marge (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Journée complète -> 0 pointage -> Heure actuelle <= Heure arrivée matin + marge -> Pas d'anomalie
        """
        # Définir l'heure actuelle à 8h10 (avant l'heure de début + marge)
        current_time = datetime.combine(self.today, time(8, 10))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_no_schedule_detail_no_anomaly(self):
        """
        Test pour un jour sans détail de planning (aucune anomalie ne doit être créée)
        Arbre de décision: Planning actif -> Pas de détail pour ce jour -> Pas d'anomalie
        """
        # Supprimer les détails du planning pour aujourd'hui
        ScheduleDetail.objects.filter(
            schedule=self.full_day_schedule,
            day_of_week=self.today_weekday
        ).delete()
        
        # Définir l'heure actuelle à 8h30
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now
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

    def test_dry_run_no_anomaly_created(self):
        """
        Test en mode dry-run (aucune anomalie ne doit être créée)
        """
        # Définir l'heure actuelle à 8h30
        current_time = datetime.combine(self.today, time(8, 30))
        
        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())
        
        try:
            # Appeler la commande en mode dry-run
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee_full_day.id), '--dry-run', stdout=out)
            
            # Vérifier qu'aucune anomalie n'a été créée
            anomalies = Anomaly.objects.filter(
                employee=self.employee_full_day,
                site=self.site,
                date=self.today
            )
            self.assertEqual(anomalies.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now
