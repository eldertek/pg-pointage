"""
Tests for anomalies related to fixed schedules.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
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
        
        # Create anomaly for late arrival
        self._create_anomaly(
            anomaly_type=Anomaly.AnomalyType.LATE,
            minutes=10,
            description='Retard de 10 minutes.',
            timesheet=timesheet
        )
        
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
        # First, test automatic anomaly creation at 8:15 (margin limit)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.monday_date.replace(hour=8, minute=15)
            
            # Simulate the automatic check that would happen at 8:15
            anomaly = self._create_anomaly(
                anomaly_type=Anomaly.AnomalyType.LATE,
                minutes=15,
                description='Retard de 15 minutes.'
            )
            
            # Create alert for the anomaly
            Alert.objects.create(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly,
                alert_type='LATE',
                message='Alerte de retard',
                status='PENDING'
            )
            
            # Verify alert is created
            alerts = Alert.objects.filter(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly
            )
            self.assertEqual(alerts.count(), 1)
        
        # Now employee clocks in at 8:22 (22 minutes late, outside 15-minute margin)
        arrival_time = time(8, 22)
        timesheet = self._create_timesheet(arrival_time)
        
        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_late)
        self.assertEqual(timesheet.late_minutes, 22)
        
        # Update the anomaly with the actual arrival time
        anomaly.refresh_from_db()
        anomaly.timesheet = timesheet
        anomaly.minutes = 22
        anomaly.description = f'Retard de {timesheet.late_minutes} minutes.'
        anomaly.save()
        
        # Verify anomaly is updated
        anomaly.refresh_from_db()
        self.assertEqual(anomaly.minutes, 22)
        self.assertEqual(anomaly.timesheet, timesheet)

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
        
        # Create anomaly for early departure
        anomaly = self._create_anomaly(
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE,
            minutes=13,
            description='Départ anticipé de 13 minutes.',
            timesheet=timesheet
        )
        
        # Create alert for the anomaly
        Alert.objects.create(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly,
            alert_type='EARLY_DEPARTURE',
            message='Alerte de départ anticipé',
            status='PENDING'
        )
        
        # Verify anomaly is created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.monday_date.date(),
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertEqual(anomalies.first().minutes, 13)
        
        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
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
            scan_type=Timesheet.ScanType.QR_CODE,
            is_out_of_schedule=True
        )
        
        # Create anomaly for out of schedule
        anomaly = self._create_anomaly(
            anomaly_type=Anomaly.AnomalyType.OTHER,
            minutes=0,
            description='Pointage hors planning.',
            timesheet=timesheet,
            date=sunday_date.date()
        )
        
        # Create alert for the anomaly
        Alert.objects.create(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly,
            alert_type='OTHER',
            message='Alerte de pointage hors planning',
            status='PENDING'
        )
        
        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_out_of_schedule)
        
        # Verify anomaly is created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=sunday_date.date(),
            anomaly_type=Anomaly.AnomalyType.OTHER,
            description__contains='Pointage hors planning'
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
        )
        self.assertEqual(alerts.count(), 1)

    def test_missed_clock_in(self):
        """Test Workflow 6: Missed clock-in."""
        # Simulate the automatic check that would happen at 8:15
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.monday_date.replace(hour=8, minute=15)
            
            # Create anomaly for missing arrival
            anomaly = self._create_anomaly(
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                minutes=0,
                description='Aucun pointage d\'arrivée enregistré.'
            )
            
            # Create alert for the anomaly
            Alert.objects.create(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly,
                alert_type='MISSING_ARRIVAL',
                message='Alerte d\'absence de pointage',
                status='PENDING'
            )
            
            # Verify alert is created for the employee
            alerts = Alert.objects.filter(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly
            )
            self.assertEqual(alerts.count(), 1)
        
        # Employee clocks in late at 8:19 after seeing the notification
        arrival_time = time(8, 19)
        timesheet = self._create_timesheet(arrival_time)
        
        # Verify timesheet is created correctly
        self.assertEqual(timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertTrue(timesheet.is_late)
        self.assertEqual(timesheet.late_minutes, 19)
        
        # Update the anomaly with the actual arrival time
        anomaly.refresh_from_db()
        anomaly.timesheet = timesheet
        anomaly.anomaly_type = Anomaly.AnomalyType.LATE
        anomaly.minutes = 19
        anomaly.description = f'Retard de {timesheet.late_minutes} minutes.'
        anomaly.save()
        
        # Verify anomaly is updated
        anomaly.refresh_from_db()
        self.assertEqual(anomaly.anomaly_type, Anomaly.AnomalyType.LATE)
        self.assertEqual(anomaly.minutes, 19)
        self.assertEqual(anomaly.timesheet, timesheet)

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
        
        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)
        
        # Employee clocks in at 9:00
        arrival_time = time(9, 0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=tuesday_date.replace(hour=9, minute=0),
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Employee clocks out at 10:35 (95 minutes later)
        departure_time = time(10, 35)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=tuesday_date.replace(hour=10, minute=35),
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Verify both timesheets are created correctly
        self.assertEqual(arrival_timesheet.entry_type, Timesheet.EntryType.ARRIVAL)
        self.assertEqual(departure_timesheet.entry_type, Timesheet.EntryType.DEPARTURE)
        
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
        
        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)
        
        # Employee clocks in at 8:15
        arrival_time = time(8, 15)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=tuesday_date.replace(hour=8, minute=15),
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Employee clocks out at 9:00 (45 minutes later)
        departure_time = time(9, 0)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=tuesday_date.replace(hour=9, minute=0),
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Create anomaly for insufficient duration
        anomaly = self._create_anomaly(
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS,
            minutes=45,
            description='Durée de présence insuffisante : 45 minutes au lieu de 90 minutes.',
            timesheet=departure_timesheet,
            date=tuesday_date.date()
        )
        
        # Create alert for the anomaly
        Alert.objects.create(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly,
            alert_type='INSUFFICIENT_HOURS',
            message='Alerte de durée insuffisante',
            status='PENDING'
        )
        
        # Verify anomaly is created for insufficient duration
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS
        )
        self.assertEqual(anomalies.count(), 1)
        self.assertEqual(anomalies.first().minutes, 45)
        
        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
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
        
        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)
        
        # Employee clocks in at 10:00 (only one clock)
        arrival_time = time(10, 0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=tuesday_date.replace(hour=10, minute=0),
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Create anomaly for missing departure
        anomaly = self._create_anomaly(
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
            minutes=0,
            description='Pointage de départ manquant.',
            timesheet=arrival_timesheet,
            date=tuesday_date.date()
        )
        
        # Create alert for the anomaly
        Alert.objects.create(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly,
            alert_type='MISSING_DEPARTURE',
            message='Alerte de départ manquant',
            status='PENDING'
        )
        
        # Verify anomaly is created for missing departure
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1)
        
        # Verify alert is created
        alerts = Alert.objects.filter(
            employee=self.employee,
            site=self.site,
            anomaly=anomalies.first()
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
        
        # Set up a Tuesday date
        tuesday_date = self.monday_date + timedelta(days=1)
        
        # Simulate end of day check
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = tuesday_date.replace(hour=23, minute=59)
            
            # Create anomaly for missing attendance
            anomaly = self._create_anomaly(
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                minutes=0,
                description='Aucun pointage enregistré pour ce jour.',
                date=tuesday_date.date()
            )
            
            # Create alert for the anomaly
            Alert.objects.create(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly,
                alert_type='MISSING_ARRIVAL',
                message='Alerte d\'absence de pointage',
                status='PENDING'
            )
            
            # Verify anomaly is created for missing attendance
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=tuesday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL
            )
            self.assertEqual(anomalies.count(), 1)
            
            # Verify alert is created
            alerts = Alert.objects.filter(
                employee=self.employee,
                site=self.site,
                anomaly=anomalies.first()
            )
            self.assertEqual(alerts.count(), 1)


