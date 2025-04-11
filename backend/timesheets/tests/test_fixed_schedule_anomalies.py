"""
Tests for anomalies related to fixed schedules.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from organizations.models import Organization
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from timesheets.models import Timesheet, Anomaly
from alerts.models import Alert
from unittest.mock import patch

User = get_user_model()

class FixedScheduleAnomalyTestCase(TestCase):
    """Test case for anomalies related to fixed schedules."""

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

        # Create manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            role=User.Role.MANAGER,
            first_name='Test',
            last_name='Manager'
        )
        self.manager.organizations.add(self.organization)

        # Associate employee with site
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            is_active=True
        )

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

        # Calculate late/early departure status
        if entry_type == Timesheet.EntryType.ARRIVAL:
            schedule_start = self.monday_date.replace(hour=8, minute=0)
            if timestamp > schedule_start:
                timesheet.is_late = True
                timesheet.late_minutes = int((timestamp - schedule_start).total_seconds() / 60)
            else:
                timesheet.is_late = False
                timesheet.late_minutes = 0
        else:  # DEPARTURE
            schedule_end = self.monday_date.replace(hour=12, minute=0)
            if timestamp < schedule_end:
                timesheet.is_early_departure = True
                timesheet.early_departure_minutes = int((schedule_end - timestamp).total_seconds() / 60)
            else:
                timesheet.is_early_departure = False
                timesheet.early_departure_minutes = 0

        timesheet.save()
        return timesheet

    def _create_anomaly(self, anomaly_type, minutes=0, description=None, timesheet=None, date=None):
        """Helper method to create an anomaly."""
        if date is None:
            date = self.monday_date.date()

        return Anomaly.objects.create(
            employee=self.employee,
            site=self.site,
            date=date,
            anomaly_type=anomaly_type,
            minutes=minutes,
            description=description,
            timesheet=timesheet,
            status=Anomaly.AnomalyStatus.PENDING
        )

    def _scan_anomalies(self, start_date=None, end_date=None, employee_id=None, site_id=None):
        """Helper method to call the scan-anomalies API endpoint."""
        if start_date is None:
            start_date = self.monday_date.date()
        if end_date is None:
            end_date = start_date
        if employee_id is None:
            employee_id = self.employee.id
        if site_id is None:
            site_id = self.site.id

        # Create API client and authenticate as manager
        client = APIClient()
        client.force_authenticate(user=self.manager)

        # Call the scan-anomalies endpoint
        response = client.post(
            reverse('scan-anomalies'),
            {
                'start_date': start_date,
                'end_date': end_date,
                'site': site_id,
                'employee': employee_id
            },
            format='json'
        )

        return response

    def test_on_time_arrival(self):
        """Test Workflow 1: On-time arrival within scheduled hours."""
        # Employee clocks in at 7:55 (5 minutes early)
        arrival_time = time(7, 55)
        timesheet = self._create_timesheet(arrival_time)

        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertFalse(timesheet.is_late)
        self.assertEqual(timesheet.late_minutes, 0)

        # Verify no anomalies are created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date()
        )
        self.assertEqual(anomalies.count(), 0)

    def test_late_arrival_within_margin(self):
        """Test Workflow 2: Late arrival within the allowed margin."""
        # Employee clocks in at 8:10 (10 minutes late, within 15-minute margin)
        arrival_time = time(8, 10)
        timesheet = self._create_timesheet(arrival_time)

        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_late)
        self.assertEqual(timesheet.late_minutes, 10)

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies()

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify anomaly is created but no alert is sent (within margin)
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.LATE
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertEqual(anomalies.first().minutes, 10)

        # Check that no alert was created (since it's within margin)
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 0)

    def test_late_arrival_outside_margin(self):
        """Test Workflow 3: Late arrival outside the allowed margin."""
        # Employee clocks in at 8:22 (22 minutes late, outside 15-minute margin)
        arrival_time = time(8, 22)
        timesheet = self._create_timesheet(arrival_time)

        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_late)
        self.assertEqual(timesheet.late_minutes, 22)

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies()

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify anomaly is created for late arrival
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.LATE
        )
        self.assertEqual(anomalies.count(), 1)

        # Get the anomaly
        anomaly = anomalies.first()

        # Verify anomaly details
        self.assertEqual(anomaly.minutes, 22)
        self.assertEqual(anomaly.timesheet, timesheet)

        # Verify alert is created for late arrival outside margin
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)

    def test_early_departure_outside_margin(self):
        """Test Workflow 4: Early departure outside the allowed margin."""
        # Employee clocks in at 8:00 (on time)
        arrival_time = time(8, 0)
        self._create_timesheet(arrival_time)

        # Employee clocks out at 11:47 (13 minutes early, outside 10-minute margin)
        departure_time = time(11, 47)
        timesheet = self._create_timesheet(departure_time, Timesheet.EntryType.DEPARTURE)

        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.DEPARTURE)
        self.assertTrue(timesheet.is_early_departure)
        self.assertEqual(timesheet.early_departure_minutes, 13)

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies()

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify anomaly is created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Get the anomaly
        anomaly = anomalies.first()

        # Verify anomaly details
        self.assertEqual(anomaly.minutes, 13)
        self.assertEqual(anomaly.timesheet, timesheet)

        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)

    def test_clock_in_outside_schedule(self):
        """Test Workflow 5: Clock-in on a day with no schedule."""
        # Create a Sunday date (no schedule configured)
        sunday_date = self.monday_date - timedelta(days=1)

        # Employee clocks in on Sunday at 8:00
        timestamp = sunday_date.replace(hour=8, minute=0)
        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
            # Note: is_out_of_schedule should be set by the system, not manually
        )

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies(start_date=sunday_date.date(), end_date=sunday_date.date())

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Refresh timesheet from database
        timesheet.refresh_from_db()

        # Verify timesheet is marked as out of schedule
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_out_of_schedule)

        # Verify anomaly is created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=sunday_date.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER,
            description__contains='hors planning'
        )
        self.assertEqual(anomalies.count(), 1)

        # Get the anomaly
        anomaly = anomalies.first()

        # Verify anomaly is linked to the timesheet
        self.assertEqual(anomaly.timesheet, timesheet)

        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)

    def test_missed_clock_in(self):
        """Test Workflow 6: Missed clock-in."""
        # First, scan for anomalies without any timesheet entries
        # This should detect a missing arrival
        with patch('django.utils.timezone.now') as mock_now:
            # Set the time to 8:15 to simulate the check that would happen after the expected arrival time
            mock_now.return_value = self.monday_date.replace(hour=8, minute=15)

            # Call the scan-anomalies API to detect missing arrival
            response = self._scan_anomalies(start_date=self.monday_date.date(), end_date=self.monday_date.date(), employee_id=self.employee.id, site_id=self.site.id)

            # Verify the response
            self.assertEqual(response.status_code, 200)

            # Verify anomaly is created for missing arrival
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.monday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

            # Get the anomaly
            anomaly = anomalies.first()

            # Verify alert is created for the employee
            alerts = Alert.objects.filter(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly
            )
            self.assertEqual(alerts.count(), 1)

        # Now employee clocks in late at 8:19 after seeing the notification
        arrival_time = time(8, 19)
        timesheet = self._create_timesheet(arrival_time)

        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_late)
        self.assertEqual(timesheet.late_minutes, 19)

        # Call the scan-anomalies API again to update the anomaly
        response = self._scan_anomalies()

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify the MISSING_ARRIVAL anomaly has been deleted
        missing_arrival_anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
        )
        self.assertEqual(missing_arrival_anomalies.count(), 0)

        # Verify a LATE anomaly has been created
        late_anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.LATE
        )
        self.assertEqual(late_anomalies.count(), 1)

        # Get the late anomaly
        late_anomaly = late_anomalies.first()

        # Verify anomaly details
        self.assertEqual(late_anomaly.minutes, 19)
        self.assertEqual(late_anomaly.timesheet, timesheet)

    def test_offline_clock_in(self):
        """Test Workflow 8: Offline clock-in."""
        # Employee clocks in at 8:00 without network
        arrival_time = time(8, 0)
        timesheet = self._create_timesheet(arrival_time)

        # Simulate offline storage
        timesheet.created_offline = True
        timesheet.save()

        # Verify timesheet is created correctly with offline flag
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.created_offline)

        # Simulate network restoration and sync
        timesheet.synced_at = timezone.now()
        timesheet.save()

        # Verify timesheet is now marked as synced
        timesheet.refresh_from_db()
        self.assertIsNotNone(timesheet.synced_at)

        # Call the scan-anomalies API to check for anomalies
        response = self._scan_anomalies()

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify no anomalies are created for offline sync
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date()
        )
        self.assertEqual(anomalies.count(), 0)

    def test_frequency_schedule_normal_passage(self):
        """Test Workflow 9: Normal passage with frequency schedule."""
        # Create frequency schedule for Tuesday (90 minutes duration)
        tuesday_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )

        ScheduleDetail.objects.create(
            schedule=tuesday_schedule,
            day_of_week=1,  # Tuesday
            day_type=ScheduleDetail.DayType.FULL,
            frequency_duration=90
        )

        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=tuesday_schedule,
            is_active=True
        )

        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)

        # Employee clocks in at 9:00
        timestamp_in = tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_in,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Employee clocks out at 10:35 (95 minutes later)
        timestamp_out = tuesday_date.replace(hour=10, minute=35)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_out,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Verify both timesheets are created correctly
        self.assertEqual(arrival_timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertEqual(departure_timesheet.entry_type, Timesheet.EntryType.DEPARTURE)

        # Call the scan-anomalies API to check for anomalies
        response = self._scan_anomalies(start_date=tuesday_date.date(), end_date=tuesday_date.date())

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify no anomalies are created (duration > 90 minutes)
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=tuesday_date.date()
        )
        self.assertEqual(anomalies.count(), 0)

    def test_frequency_schedule_insufficient_duration(self):
        """Test Workflow 10: Passage with insufficient duration."""
        # Create frequency schedule for Tuesday (90 minutes duration)
        tuesday_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )

        ScheduleDetail.objects.create(
            schedule=tuesday_schedule,
            day_of_week=1,  # Tuesday
            day_type=ScheduleDetail.DayType.FULL,
            frequency_duration=90
        )

        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=tuesday_schedule,
            is_active=True
        )

        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)

        # Employee clocks in at 8:15
        timestamp_in = tuesday_date.replace(hour=8, minute=15)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_in,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Employee clocks out at 9:00 (45 minutes later)
        timestamp_out = tuesday_date.replace(hour=9, minute=0)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_out,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies(start_date=tuesday_date.date(), end_date=tuesday_date.date())

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify anomaly is created for insufficient duration
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies.count(), 1)

        # Get the anomaly
        anomaly = anomalies.first()

        # Verify anomaly details
        self.assertEqual(anomaly.minutes, 45)
        self.assertEqual(anomaly.timesheet, departure_timesheet)

        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_schedule_single_clock(self):
        """Test Workflow 11: Single clock-in or clock-out."""
        # Create frequency schedule for Tuesday
        tuesday_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )

        ScheduleDetail.objects.create(
            schedule=tuesday_schedule,
            day_of_week=1,  # Tuesday
            day_type=ScheduleDetail.DayType.FULL,
            frequency_duration=60
        )

        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=tuesday_schedule,
            is_active=True
        )

        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)

        # Employee clocks in at 10:00 (only one clock)
        timestamp_in = tuesday_date.replace(hour=10, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_in,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies(start_date=tuesday_date.date(), end_date=tuesday_date.date())

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify anomaly is created for missing departure
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Get the anomaly
        anomaly = anomalies.first()

        # Verify anomaly is linked to the timesheet
        self.assertEqual(anomaly.timesheet, arrival_timesheet)

        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly
        )
        self.assertEqual(alerts.count(), 1)

    def test_frequency_schedule_no_clocks(self):
        """Test Workflow 12: No clocks on scheduled day."""
        # Create frequency schedule for Tuesday
        tuesday_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )

        ScheduleDetail.objects.create(
            schedule=tuesday_schedule,
            day_of_week=1,  # Tuesday
            day_type=ScheduleDetail.DayType.FULL,
            frequency_duration=60
        )

        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=tuesday_schedule,
            is_active=True
        )

        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)

        # Simulate end of day check
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = tuesday_date.replace(hour=23, minute=59)

            # Call the scan-anomalies API to detect missing arrival
            response = self._scan_anomalies(start_date=tuesday_date.date(), end_date=tuesday_date.date())

            # Verify the response
            self.assertEqual(response.status_code, 200)

            # Verify anomaly is created for missing attendance
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=tuesday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)

            # Get the anomaly
            anomaly = anomalies.first()

            # Verify alert is created
            alerts = Alert.objects.filter(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly
            )
            self.assertEqual(alerts.count(), 1)

    def test_early_departure_split_shift(self):
        """Test Workflow 13: Early departure with split shift schedule.

        This test verifies that when an employee with a split shift (morning/afternoon)
        clocks out during the morning period, the early departure calculation is correctly
        based on the end time of the morning shift (end_time_1) rather than the start time
        of the afternoon shift (start_time_2).

        Bug scenario: Employee has schedule 9:00-12:00 and 14:00-17:00.
        When clocking out at 10:00 (during morning shift), the system incorrectly calculates
        early departure as 240 minutes (14:00 - 10:00) instead of 120 minutes (12:00 - 10:00).
        """
        # Create a split shift schedule for Monday (9:00-12:00 AM, 14:00-17:00 PM)
        split_schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True,
            early_departure_margin=10  # 10 minutes margin for early departure
        )

        # Monday schedule with split shift (morning and afternoon)
        ScheduleDetail.objects.create(
            schedule=split_schedule,
            day_of_week=0,  # Monday
            day_type=ScheduleDetail.DayType.FULL,
            start_time_1=time(9, 0),   # 9:00 AM
            end_time_1=time(12, 0),    # 12:00 PM
            start_time_2=time(14, 0),  # 2:00 PM
            end_time_2=time(17, 0)     # 5:00 PM
        )

        # Associate employee with the split shift schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=split_schedule,
            is_active=True
        )

        # Employee clocks in at 9:00 (on time)
        timestamp_in = self.monday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_in,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Employee clocks out at 10:00 (2 hours early from morning end time)
        timestamp_out = self.monday_date.replace(hour=10, minute=0)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=timestamp_out,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )

        # Call the scan-anomalies API to detect anomalies
        response = self._scan_anomalies()

        # Verify the response
        self.assertEqual(response.status_code, 200)

        # Verify timesheet is created correctly
        departure_timesheet.refresh_from_db()
        self.assertEqual(departure_timesheet.entry_type, Timesheet.EntryType.DEPARTURE)
        self.assertTrue(departure_timesheet.is_early_departure)

        # Verify early departure minutes are calculated correctly (120 minutes, not 240)
        self.assertEqual(departure_timesheet.early_departure_minutes, 120)

        # Verify anomaly is created with correct minutes
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)

        # Get the anomaly
        anomaly = anomalies.first()

        # Verify anomaly details
        self.assertEqual(anomaly.minutes, 120)
        self.assertEqual(anomaly.timesheet, departure_timesheet)

        # This test verifies that the early departure calculation is based on the end time
        # of the current shift period (morning end time) rather than the start time of the
        # next shift period (afternoon start time)

