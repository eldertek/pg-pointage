"""
Tests pour vérifier que la commande check_minute_anomalies suit l'arbre de décision
défini dans .cursor/rules/minute_anomalies.mdc
"""
from datetime import datetime, time, timedelta
from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization
from timesheets.management.commands.check_minute_anomalies import Command

User = get_user_model()

class CheckMinuteAnomaliesTestCase(TestCase):
    """Tests pour la commande check_minute_anomalies"""

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

        # Créer un planning fixe
        self.fixed_schedule = Schedule.objects.create(
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

        # Associer l'employé au site avec le planning fixe
        self.site_employee_fixed = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.fixed_schedule,
            is_active=True
        )

        # Créer un autre employé pour le planning fréquence
        self.employee2 = User.objects.create_user(
            username="employee2",
            email="employee2@example.com",
            password="password",
            first_name="Test2",
            last_name="Employee2",
            role="EMPLOYEE"
        )

        # Associer le deuxième employé au site avec le planning fréquence
        self.site_employee_frequency = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee2,
            schedule=self.frequency_schedule,
            is_active=True
        )

        # Créer les détails du planning fixe pour aujourd'hui (journée complète)
        today_weekday = timezone.now().weekday()
        self.schedule_detail_full = ScheduleDetail.objects.create(
            schedule=self.fixed_schedule,
            day_of_week=today_weekday,
            day_type=ScheduleDetail.DayType.FULL,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Créer les détails du planning fixe pour demain (demi-journée matin)
        tomorrow_weekday = (today_weekday + 1) % 7
        self.schedule_detail_am = ScheduleDetail.objects.create(
            schedule=self.fixed_schedule,
            day_of_week=tomorrow_weekday,
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

    def test_no_anomaly_before_start_time(self):
        """Test qu'aucune anomalie n'est créée avant l'heure de début + marge"""
        # Définir l'heure actuelle à 8h00 (heure de début)
        current_time = datetime.combine(timezone.now().date(), time(8, 0))

        # Appeler la commande avec l'heure actuelle
        out = StringIO()
        call_command('check_minute_anomalies', stdout=out)

        # Vérifier qu'aucune anomalie n'a été créée
        self.assertEqual(Anomaly.objects.count(), 0)

    def test_anomaly_after_start_time_plus_margin(self):
        """Test qu'une anomalie est créée après l'heure de début + marge"""
        # Définir l'heure actuelle à 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(timezone.now().date(), time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', stdout=out)

            # Vérifier qu'une anomalie a été créée
            self.assertEqual(Anomaly.objects.count(), 1)

            # Vérifier les détails de l'anomalie
            anomaly = Anomaly.objects.first()
            self.assertEqual(anomaly.employee, self.employee)
            self.assertEqual(anomaly.site, self.site)
            self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.MISSING_ARRIVAL)
            self.assertEqual(anomaly.date, timezone.now().date())
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_no_anomaly_with_existing_timesheet(self):
        """Test qu'aucune anomalie n'est créée si un pointage existe déjà"""
        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=5),
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Définir l'heure actuelle à 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(timezone.now().date(), time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', stdout=out)

            # Vérifier qu'aucune anomalie n'a été créée
            self.assertEqual(Anomaly.objects.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_afternoon_missing_arrival(self):
        """Test qu'une anomalie est créée pour un pointage d'après-midi manquant"""
        # Créer deux pointages (arrivée et départ du matin)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=8, minute=0),
            entry_type=Timesheet.EntryType.ARRIVAL
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timezone.now().replace(hour=12, minute=0),
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Définir l'heure actuelle à 13h16 (après l'heure de début de l'après-midi + marge)
        current_time = datetime.combine(timezone.now().date(), time(13, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', stdout=out)

            # Vérifier qu'une anomalie a été créée
            self.assertEqual(Anomaly.objects.count(), 1)

            # Vérifier les détails de l'anomalie
            anomaly = Anomaly.objects.first()
            self.assertEqual(anomaly.employee, self.employee)
            self.assertEqual(anomaly.site, self.site)
            self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.MISSING_ARRIVAL)
            self.assertEqual(anomaly.date, timezone.now().date())
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_half_day_morning_missing_arrival(self):
        """Test qu'une anomalie est créée pour un pointage manquant en demi-journée matin"""
        # Changer la date pour utiliser le planning demi-journée matin
        tomorrow = timezone.now().date() + timedelta(days=1)
        tomorrow_weekday = tomorrow.weekday()

        # Définir l'heure actuelle à demain 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(tomorrow, time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', stdout=out)

            # Vérifier qu'une anomalie a été créée
            self.assertEqual(Anomaly.objects.count(), 1)

            # Vérifier les détails de l'anomalie
            anomaly = Anomaly.objects.first()
            self.assertEqual(anomaly.employee, self.employee)
            self.assertEqual(anomaly.site, self.site)
            self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.MISSING_ARRIVAL)
            self.assertEqual(anomaly.date, tomorrow)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_no_anomaly_for_frequency_schedule(self):
        """Test qu'aucune anomalie n'est créée pour un planning de type fréquence"""
        # Définir l'heure actuelle à 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(timezone.now().date(), time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', '--employee', str(self.employee2.id), stdout=out)

            # Vérifier qu'aucune anomalie n'a été créée pour l'employé avec planning fréquence
            self.assertEqual(Anomaly.objects.filter(employee=self.employee2).count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_dry_run_mode(self):
        """Test que le mode dry-run n'enregistre pas d'anomalies"""
        # Définir l'heure actuelle à 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(timezone.now().date(), time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande en mode dry-run
            out = StringIO()
            call_command('check_minute_anomalies', '--dry-run', stdout=out)

            # Vérifier qu'aucune anomalie n'a été créée
            self.assertEqual(Anomaly.objects.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_inactive_site(self):
        """Test qu'aucune anomalie n'est créée pour un site inactif"""
        # Désactiver le site
        self.site.is_active = False
        self.site.save()

        # Définir l'heure actuelle à 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(timezone.now().date(), time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', stdout=out)

            # Vérifier qu'aucune anomalie n'a été créée
            self.assertEqual(Anomaly.objects.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now

    def test_inactive_schedule(self):
        """Test qu'aucune anomalie n'est créée pour un planning inactif"""
        # Désactiver le planning
        self.fixed_schedule.is_active = False
        self.fixed_schedule.save()

        # Définir l'heure actuelle à 8h16 (après l'heure de début + marge)
        current_time = datetime.combine(timezone.now().date(), time(8, 16))

        # Simuler l'heure actuelle
        original_now = timezone.now
        timezone.now = lambda: current_time.replace(tzinfo=timezone.get_current_timezone())

        try:
            # Appeler la commande
            out = StringIO()
            call_command('check_minute_anomalies', stdout=out)

            # Vérifier qu'aucune anomalie n'a été créée
            self.assertEqual(Anomaly.objects.count(), 0)
        finally:
            # Restaurer la fonction timezone.now
            timezone.now = original_now
