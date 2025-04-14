from datetime import datetime, time
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command

from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from users.models import User
from organizations.models import Organization


class TestCheckMissedCheckinsCommand(TestCase):
    def setUp(self):
        # Créer une organisation
        self.organization = Organization.objects.create(
            name="Test Organization",
            address="123 Test Street",
            postal_code="12345",
            city="Test City"
        )

        # Créer un site
        self.site = Site.objects.create(
            name="Test Site",
            organization=self.organization,
            address="123 Test Street",
            postal_code="12345",
            city="Test City",
            late_margin=15,
            early_departure_margin=10
        )

        # Créer un employé
        self.employee = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
            first_name="Test",
            last_name="User",
            is_active=True
        )

        # Créer un planning fixe
        self.fixed_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True,
            late_arrival_margin=15,
            early_departure_margin=10
        )

        # Créer un planning fréquence
        self.frequency_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True,
            frequency_tolerance_percentage=10
        )

        # Créer les détails du planning fixe pour le lundi (0)
        self.fixed_schedule_detail = ScheduleDetail.objects.create(
            schedule=self.fixed_schedule,
            day_of_week=0,  # Lundi
            start_time_1=time(8, 0),
            end_time_1=time(12, 0),
            start_time_2=time(13, 0),
            end_time_2=time(17, 0)
        )

        # Créer les détails du planning fréquence pour le mardi (1)
        self.frequency_schedule_detail = ScheduleDetail.objects.create(
            schedule=self.frequency_schedule,
            day_of_week=1,  # Mardi
            frequency_duration=30
        )

        # Associer l'employé au site avec le planning fixe
        self.site_employee_fixed = SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.fixed_schedule,
            is_active=True
        )

        # Date de test (lundi)
        self.monday_date = timezone.make_aware(datetime(2023, 1, 2))  # Un lundi

        # Date de test (mardi)
        self.tuesday_date = timezone.make_aware(datetime(2023, 1, 3))  # Un mardi

    def test_check_missed_checkins_fixed_schedule(self):
        """Test que la commande détecte les pointages manquants pour un planning fixe."""
        # Simuler que nous sommes lundi
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.monday_date.replace(hour=23, minute=59)

            # Exécuter la commande en mode simulation
            call_command('check_missed_checkins', '--dry-run', '--verbose')

            # Vérifier qu'aucune anomalie n'est créée en mode simulation
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.monday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 0)

            # Exécuter la commande sans le mode simulation
            call_command('check_missed_checkins')

            # Vérifier qu'une anomalie est créée pour l'arrivée manquante
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.monday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

            # Créer un pointage d'arrivée
            Timesheet.objects.create(
                employee=self.employee,
                site=self.site,
                timestamp=self.monday_date.replace(hour=8, minute=30),
                entry_type=Timesheet.EntryType.ARRIVAL,
                scan_type=Timesheet.ScanType.QR_CODE
            )

            # Exécuter la commande à nouveau
            call_command('check_missed_checkins')

            # Vérifier que l'anomalie n'est pas dupliquée
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.monday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

    def test_check_missed_checkins_frequency_schedule(self):
        """Test que la commande détecte les pointages manquants pour un planning fréquence."""
        # Simuler que nous sommes mardi
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.tuesday_date.replace(hour=23, minute=59)

            # Associer l'employé au site avec le planning fréquence
            self.site_employee_fixed.schedule = self.frequency_schedule
            self.site_employee_fixed.save()

            # Exécuter la commande
            call_command('check_missed_checkins')

            # Vérifier qu'une anomalie est créée pour l'arrivée manquante
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.tuesday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

            # Créer un pointage d'arrivée
            Timesheet.objects.create(
                employee=self.employee,
                site=self.site,
                timestamp=self.tuesday_date.replace(hour=10, minute=0),
                entry_type=Timesheet.EntryType.ARRIVAL,
                scan_type=Timesheet.ScanType.QR_CODE
            )

            # Exécuter la commande à nouveau
            call_command('check_missed_checkins')

            # Vérifier que l'anomalie n'est pas dupliquée
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.tuesday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

    def test_check_missed_checkins_with_date_parameter(self):
        """Test que la commande fonctionne avec le paramètre de date."""
        # Exécuter la commande avec une date spécifique
        call_command('check_missed_checkins', '--date', '2023-01-02')

        # Vérifier qu'une anomalie est créée pour l'arrivée manquante
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)

    def test_check_missed_checkins_with_site_parameter(self):
        """Test que la commande fonctionne avec le paramètre de site."""
        # Exécuter la commande avec un site spécifique
        call_command('check_missed_checkins', '--site', str(self.site.id), '--date', '2023-01-02')

        # Vérifier qu'une anomalie est créée pour l'arrivée manquante
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)

    def test_check_missed_checkins_with_employee_parameter(self):
        """Test que la commande fonctionne avec le paramètre d'employé."""
        # Exécuter la commande avec un employé spécifique
        call_command('check_missed_checkins', '--employee', str(self.employee.id), '--date', '2023-01-02')

        # Vérifier qu'une anomalie est créée pour l'arrivée manquante
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(anomalies.count(), 1)
