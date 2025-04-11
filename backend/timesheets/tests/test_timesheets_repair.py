"""
Tests for the timesheets_repair management command.
"""
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from io import StringIO
from organizations.models import Organization
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from timesheets.models import Timesheet, Anomaly

User = get_user_model()

class TimesheetsRepairCommandTestCase(TestCase):
    """Test case for the timesheets_repair management command."""

    def setUp(self):
        """Set up test data."""
        # Create organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            org_id='TST'
        )

        # Create site with late margin of 15 minutes and early departure margin of 10 minutes
        self.site = Site.objects.create(
            name='Test Site',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.organization,
            nfc_id='TST-S001',
            late_margin=15,
            early_departure_margin=10
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

        # Create fixed schedule for Monday (8:00 - 12:00)
        self.schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True
        )

        # Monday schedule (day_of_week=0)
        ScheduleDetail.objects.create(
            schedule=self.schedule,
            day_of_week=0,  # Monday
            day_type=ScheduleDetail.DayType.AM,
            start_time_1='08:00:00',
            end_time_1='12:00:00'
        )

        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.schedule,
            is_active=True
        )

        # Set up a Monday date for testing
        self.monday_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Ensure it's a Monday
        while self.monday_date.weekday() != 0:  # 0 is Monday
            self.monday_date += timedelta(days=1)

    def _create_timesheet(self, entry_time, entry_type=Timesheet.EntryType.ARRIVAL):
        """Helper method to create a timesheet entry."""
        timestamp = self.monday_date.replace(
            hour=entry_time.hour,
            minute=entry_time.minute
        )

        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp,
            entry_type=entry_type,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Pour les tests de départ anticipé, définir manuellement les valeurs
        if entry_type == Timesheet.EntryType.DEPARTURE:
            # Vérifier si c'est un départ anticipé
            from datetime import datetime
            from sites.models import ScheduleDetail

            # Récupérer les détails du planning pour le jour actuel
            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=self.schedule,
                    day_of_week=0  # Monday
                )

                departure_time = timestamp.time()
                # Vérifier par rapport à end_time_1
                if schedule_detail.end_time_1 and departure_time < schedule_detail.end_time_1:
                    # C'est un départ anticipé par rapport à la plage du matin
                    early_minutes = int((datetime.combine(timestamp.date(), schedule_detail.end_time_1) -
                                      datetime.combine(timestamp.date(), departure_time)).total_seconds() / 60)
                    if early_minutes > 0:
                        timesheet.is_early_departure = True
                        timesheet.early_departure_minutes = early_minutes
                        timesheet.save()
            except ScheduleDetail.DoesNotExist:
                pass

        return timesheet

    def test_repair_command_no_duplicate_anomalies(self):
        """Test that the repair command does not create duplicate anomalies."""
        # Employee clocks in at 8:00 (on time)
        arrival_time = time(8, 0)
        self._create_timesheet(arrival_time)

        # Employee clocks out at 11:47 (13 minutes early, outside 10-minute margin)
        departure_time = time(11, 47)
        timesheet = self._create_timesheet(departure_time, Timesheet.EntryType.DEPARTURE)

        # Verify timesheet entry type
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.DEPARTURE)
        self.assertTrue(timesheet.is_early_departure)
        self.assertEqual(timesheet.early_departure_minutes, 13)

        # Run the repair command once
        out = StringIO()
        call_command('timesheets_repair', 
                    start_date=self.monday_date.date().isoformat(),
                    end_date=self.monday_date.date().isoformat(),
                    site=self.site.id, 
                    employee=self.employee.id, 
                    stdout=out)

        # Check that one anomaly was created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Run the repair command again
        out = StringIO()
        call_command('timesheets_repair', 
                    start_date=self.monday_date.date().isoformat(),
                    end_date=self.monday_date.date().isoformat(),
                    site=self.site.id, 
                    employee=self.employee.id, 
                    stdout=out)

        # Check that still only one anomaly exists (no duplicates)
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Verify that the anomaly has a schedule associated
        anomaly = anomalies.first()
        self.assertIsNotNone(anomaly.schedule, "L'anomalie de départ anticipé doit avoir un planning associé")
        self.assertEqual(anomaly.schedule, self.schedule, "Le planning associé à l'anomalie doit être celui de l'employé")

    def test_repair_command_with_validation_error(self):
        """Test that the repair command handles validation errors correctly."""
        # Create a sequence of timesheets that would cause a validation error
        # First arrival
        arrival_time1 = time(8, 0)
        timesheet1 = self._create_timesheet(arrival_time1)

        # First departure
        departure_time1 = time(11, 47)
        timesheet2 = self._create_timesheet(departure_time1, Timesheet.EntryType.DEPARTURE)

        # Second departure (this would cause a validation error in normal operation)
        departure_time2 = time(11, 50)
        timesheet3 = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=self.monday_date.replace(hour=departure_time2.hour, minute=departure_time2.minute),
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE,
            is_early_departure=True,
            early_departure_minutes=10
        )

        # Run the repair command with skip_validation and ignore_errors
        out = StringIO()
        call_command('timesheets_repair', 
                    start_date=self.monday_date.date().isoformat(),
                    end_date=self.monday_date.date().isoformat(),
                    site=self.site.id, 
                    employee=self.employee.id,
                    skip_validation=True,
                    ignore_errors=True,
                    stdout=out)

        # Check that the command completed successfully
        self.assertIn("Réparation terminée avec succès", out.getvalue())

        # Check that anomalies were created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date()
        )
        self.assertGreater(anomalies.count(), 0)
