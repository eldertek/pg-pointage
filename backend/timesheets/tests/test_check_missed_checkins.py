"""
Tests pour vérifier que la commande check_missed_checkins suit l'arbre de décision
défini dans .cursor/rules/daily_anomalies.mdc
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
from timesheets.management.commands.check_missed_checkins import Command
from datetime import date

User = get_user_model()


class CheckMissedCheckinsTestCase(TestCase):
    """Tests pour vérifier que la commande check_missed_checkins suit l'arbre de décision"""

    def setUp(self):
        """Initialiser les données de test"""
        # Créer une organisation
        self.organization = Organization.objects.create(
            name="Test Organization",
            address="123 Test Street",
            postal_code="12345",
            city="Test City"
        )

        # Créer un site actif
        self.active_site = Site.objects.create(
            name="Site Actif",
            address="123 Active Street",
            postal_code="12345",
            city="Active City",
            organization=self.organization,
            is_active=True,
            late_margin=10,  # 10 minutes de marge pour les retards
            early_departure_margin=10,  # 10 minutes de marge pour les départs anticipés
            nfc_id="ACTIVE123"  # Valeur unique pour le champ nfc_id (max 10 caractères)
        )

        # Créer un site inactif
        self.inactive_site = Site.objects.create(
            name="Site Inactif",
            address="123 Inactive Street",
            postal_code="12345",
            city="Inactive City",
            organization=self.organization,
            is_active=False,
            nfc_id="INACTIVE1"  # Valeur unique pour le champ nfc_id (max 10 caractères)
        )

        # Créer un employé
        self.employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="password",
            first_name="Test",
            last_name="Employee"
        )

        # Créer un planning fixe actif (journée complète)
        self.active_fixed_schedule_full = Schedule.objects.create(
            site=self.active_site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True,
            late_arrival_margin=10,
            early_departure_margin=10
        )

        # Créer un planning fixe actif (demi-journée matin)
        self.active_fixed_schedule_am = Schedule.objects.create(
            site=self.active_site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True,
            late_arrival_margin=10,
            early_departure_margin=10
        )

        # Créer un planning fixe actif (demi-journée après-midi)
        self.active_fixed_schedule_pm = Schedule.objects.create(
            site=self.active_site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True,
            late_arrival_margin=10,
            early_departure_margin=10
        )

        # Créer un planning fixe inactif
        self.inactive_fixed_schedule = Schedule.objects.create(
            site=self.active_site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=False
        )

        # Créer un planning fréquence actif
        self.active_frequency_schedule = Schedule.objects.create(
            site=self.active_site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True,
            frequency_tolerance_percentage=10
        )

        # Créer un planning fréquence inactif
        self.inactive_frequency_schedule = Schedule.objects.create(
            site=self.active_site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=False
        )

        # Créer les détails de planning pour aujourd'hui (jour 0 = lundi)
        today_weekday = timezone.now().weekday()

        # Détails pour le planning fixe actif (journée complète)
        self.schedule_detail_fixed_full = ScheduleDetail.objects.create(
            schedule=self.active_fixed_schedule_full,
            day_of_week=today_weekday,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Détails pour le planning fixe actif (demi-journée matin)
        self.schedule_detail_fixed_am = ScheduleDetail.objects.create(
            schedule=self.active_fixed_schedule_am,
            day_of_week=today_weekday,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=None,
            end_time_2=None
        )

        # Détails pour le planning fixe actif (demi-journée après-midi)
        self.schedule_detail_fixed_pm = ScheduleDetail.objects.create(
            schedule=self.active_fixed_schedule_pm,
            day_of_week=today_weekday,
            start_time_1=None,
            end_time_1=None,
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Détails pour le planning fixe inactif
        self.schedule_detail_fixed_inactive = ScheduleDetail.objects.create(
            schedule=self.inactive_fixed_schedule,
            day_of_week=today_weekday,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

        # Détails pour le planning fréquence actif
        self.schedule_detail_frequency = ScheduleDetail.objects.create(
            schedule=self.active_frequency_schedule,
            day_of_week=today_weekday,
            frequency_duration=240  # 4 heures (240 minutes)
        )

        # Détails pour le planning fréquence inactif
        self.schedule_detail_frequency_inactive = ScheduleDetail.objects.create(
            schedule=self.inactive_frequency_schedule,
            day_of_week=today_weekday,
            frequency_duration=240  # 4 heures (240 minutes)
        )

        # Créer un détail de planning pour un jour différent (pour tester les jours non planifiés)
        tomorrow_weekday = (today_weekday + 1) % 7
        self.schedule_detail_tomorrow = ScheduleDetail.objects.create(
            schedule=self.active_fixed_schedule_full,
            day_of_week=tomorrow_weekday,
            start_time_1=time(8, 0),  # 8h00
            end_time_1=time(12, 0),   # 12h00
            start_time_2=time(13, 0),  # 13h00
            end_time_2=time(17, 0)    # 17h00
        )

    def call_command(self, *args, **kwargs):
        """Appeler la commande check_missed_checkins avec les arguments spécifiés"""
        out = StringIO()
        call_command(
            'check_missed_checkins',
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs
        )
        return out.getvalue()

    def test_inactive_site(self):
        """Test: Vérifier qu'aucune anomalie n'est générée pour un site inactif"""
        # Associer l'employé au site inactif
        SiteEmployee.objects.create(
            site=self.inactive_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command(dry_run=True, verbose=True)

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.inactive_site
        )
        self.assertEqual(anomalies.count(), 0)

    def test_site_with_future_activation_date(self):
        """Test: Vérifier qu'aucune anomalie n'est générée pour un site avec date d'activation future"""
        # Créer un site avec date d'activation future
        future_site = Site.objects.create(
            name="Site Activation Future",
            address="123 Future Street",
            postal_code="12345",
            city="Future City",
            organization=self.organization,
            is_active=True,
            activation_start_date=date.today().replace(year=date.today().year + 1),  # Année prochaine
            nfc_id="FUTURE123"  # Valeur unique pour le champ nfc_id
        )

        # Associer l'employé au site avec activation future
        SiteEmployee.objects.create(
            site=future_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command(dry_run=True, verbose=True)

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=future_site
        )
        self.assertEqual(anomalies.count(), 0)

    def test_site_with_past_activation_end_date(self):
        """Test: Vérifier qu'aucune anomalie n'est générée pour un site avec date de fin d'activation passée"""
        # Créer un site avec date de fin d'activation passée
        past_site = Site.objects.create(
            name="Site Activation Passée",
            address="123 Past Street",
            postal_code="12345",
            city="Past City",
            organization=self.organization,
            is_active=True,
            activation_end_date=date.today().replace(year=date.today().year - 1),  # Année dernière
            nfc_id="PAST12345"  # Valeur unique pour le champ nfc_id
        )

        # Associer l'employé au site avec activation passée
        SiteEmployee.objects.create(
            site=past_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command(dry_run=True, verbose=True)

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=past_site
        )
        self.assertEqual(anomalies.count(), 0)

    def test_inactive_schedule(self):
        """Test: Vérifier qu'aucune anomalie n'est générée pour un planning inactif"""
        # Associer l'employé au site actif avec un planning inactif
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.inactive_fixed_schedule,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command(dry_run=True, verbose=True)

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.inactive_fixed_schedule
        )
        self.assertEqual(anomalies.count(), 0)

    def test_unplanned_day(self):
        """Test: Vérifier qu'aucune anomalie n'est générée pour un jour non planifié"""
        # Associer l'employé au site actif avec un planning actif
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Supprimer le détail de planning pour aujourd'hui
        self.schedule_detail_fixed_full.delete()

        # Exécuter la commande
        output = self.call_command(dry_run=True, verbose=True)

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_full
        )
        self.assertEqual(anomalies.count(), 0)

    def test_fixed_schedule_full_day_no_checkins(self):
        """Test: Vérifier qu'une anomalie est créée pour un planning journalier sans pointages"""
        # Associer l'employé au site actif avec un planning journalier
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_full,
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)

    def test_fixed_schedule_full_day_partial_checkins(self):
        """Test: Vérifier qu'une anomalie est créée pour un planning journalier avec pointages partiels"""
        # Associer l'employé au site actif avec un planning journalier
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.now().replace(hour=8, minute=0)
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'une anomalie a été créée pour le départ manquant
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_full,
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

    def test_fixed_schedule_full_day_complete_checkins(self):
        """Test: Vérifier qu'aucune anomalie n'est créée pour un planning journalier avec tous les pointages"""
        # Associer l'employé au site actif avec un planning journalier
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_full,
            is_active=True
        )

        # Créer les pointages complets pour la journée
        today = timezone.now().date()
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(8, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.DEPARTURE,
            timestamp=timezone.make_aware(datetime.combine(today, time(12, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(13, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.DEPARTURE,
            timestamp=timezone.make_aware(datetime.combine(today, time(17, 0)))
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_full
        )
        self.assertEqual(anomalies.count(), 0)

    def test_fixed_schedule_half_day_am_no_checkins(self):
        """Test: Vérifier qu'une anomalie est créée pour un planning demi-journée matin sans pointages"""
        # Associer l'employé au site actif avec un planning demi-journée matin
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_am,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_am,
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)

    def test_fixed_schedule_half_day_am_partial_checkins(self):
        """Test: Vérifier qu'une anomalie est créée pour un planning demi-journée matin avec pointage partiel"""
        # Associer l'employé au site actif avec un planning demi-journée matin
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_am,
            is_active=True
        )

        # Créer un pointage d'arrivée
        today = timezone.now().date()
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(8, 0)))
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'une anomalie a été créée pour le départ manquant
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_am,
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

    def test_fixed_schedule_half_day_am_complete_checkins(self):
        """Test: Vérifier qu'aucune anomalie n'est créée pour un planning demi-journée matin avec tous les pointages"""
        # Associer l'employé au site actif avec un planning demi-journée matin
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_fixed_schedule_am,
            is_active=True
        )

        # Créer les pointages complets pour la demi-journée
        today = timezone.now().date()
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(8, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.DEPARTURE,
            timestamp=timezone.make_aware(datetime.combine(today, time(12, 0)))
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_fixed_schedule_am
        )
        self.assertEqual(anomalies.count(), 0)

    def test_frequency_schedule_no_checkins(self):
        """Test: Vérifier qu'une anomalie est créée pour un planning fréquence sans pointages"""
        # Associer l'employé au site actif avec un planning fréquence
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_frequency_schedule,
            is_active=True
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_frequency_schedule,
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertIn("Passage manqué", anomalies.first().description)

    def test_frequency_schedule_one_checkin(self):
        """Test: Vérifier qu'une anomalie est créée pour un planning fréquence avec un seul pointage"""
        # Associer l'employé au site actif avec un planning fréquence
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_frequency_schedule,
            is_active=True
        )

        # Créer un pointage d'arrivée
        today = timezone.now().date()
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(8, 0)))
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'une anomalie a été créée pour le départ manquant
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_frequency_schedule,
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertIn("Pointage manquant", anomalies.first().description)

    def test_frequency_schedule_two_checkins(self):
        """Test: Vérifier qu'aucune anomalie n'est créée pour un planning fréquence avec deux pointages"""
        # Associer l'employé au site actif avec un planning fréquence
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_frequency_schedule,
            is_active=True
        )

        # Créer les pointages complets
        today = timezone.now().date()
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(8, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.DEPARTURE,
            timestamp=timezone.make_aware(datetime.combine(today, time(12, 0)))
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_frequency_schedule
        )
        self.assertEqual(anomalies.count(), 0)

    def test_frequency_schedule_multiple_checkins(self):
        """Test: Vérifier qu'aucune anomalie n'est créée pour un planning fréquence avec plus de deux pointages"""
        # Associer l'employé au site actif avec un planning fréquence
        SiteEmployee.objects.create(
            site=self.active_site,
            employee=self.employee,
            schedule=self.active_frequency_schedule,
            is_active=True
        )

        # Créer plusieurs pointages qui respectent la durée minimale requise (240 minutes)
        today = timezone.now().date()
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(8, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.DEPARTURE,
            timestamp=timezone.make_aware(datetime.combine(today, time(12, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.ARRIVAL,
            timestamp=timezone.make_aware(datetime.combine(today, time(13, 0)))
        )
        Timesheet.objects.create(
            employee=self.employee,
            site=self.active_site,
            entry_type=Timesheet.EntryType.DEPARTURE,
            timestamp=timezone.make_aware(datetime.combine(today, time(17, 0)))
        )

        # Exécuter la commande
        output = self.call_command()

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.active_site,
            schedule=self.active_frequency_schedule
        )

        # Si des anomalies sont trouvées, afficher les détails pour le débogage
        if anomalies.exists():
            for anomaly in anomalies:
                print(f"Anomalie trouvée: {anomaly.anomaly_type} - {anomaly.description} - {anomaly.date}")

        self.assertEqual(anomalies.count(), 0)