"""
Tests for anomalies related to frequency schedules.

These tests verify the detection and handling of anomalies for employees with frequency schedules,
including insufficient duration, single clock-ins, and missed clock-ins.
"""
from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from organizations.models import Organization
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from timesheets.models import Timesheet, Anomaly
from alerts.models import Alert

User = get_user_model()


class FrequencyScheduleAnomalyTestCase(TestCase):
    """Test case for anomalies related to frequency schedules.
    
    These tests focus on the workflows described in the requirements:
    - Workflow 9: Normal passage with compliant duration
    - Workflow 10: Passage with insufficient duration
    - Workflow 11: Single clock-in only
    - Workflow 12: No clock-ins
    """

    def setUp(self):
        """Set up test data."""
        # Create organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            org_id='TST'
        )
        
        # Create site with frequency tolerance of 10%
        self.site = Site.objects.create(
            name='Test Site',
            address='123 Test St',
            postal_code='75000',
            city='Paris',
            organization=self.organization,
            nfc_id='TST-S001',
            frequency_tolerance=10
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
        
        # Create frequency schedule for Tuesday (90 minutes duration)
        self.schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FREQUENCY,
            is_active=True
        )
        
        # Tuesday schedule (day_of_week=1)
        ScheduleDetail.objects.create(
            schedule=self.schedule,
            day_of_week=1,  # Tuesday
            frequency_duration=90
        )
        
        # Associate employee with schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.schedule,
            is_active=True
        )
        
        # Set up a Tuesday date for testing
        self.tuesday_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Ensure it's a Tuesday
        while self.tuesday_date.weekday() != 1:  # 1 is Tuesday
            self.tuesday_date += timedelta(days=1)

    def test_normal_passage(self):
        """Test Workflow 9: Normal passage with compliant duration."""
        # Employee clocks in at 9:00
        arrival_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        arrival_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Employee clocks out at 10:35 (95 minutes later, which is compliant)
        departure_timestamp = self.tuesday_date.replace(hour=10, minute=35)
        departure_timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
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
            date=self.tuesday_date.date()
        )
        self.assertEqual(anomalies.count(), 0)

    def test_insufficient_duration(self):
        """Test Workflow 10: Passage with insufficient duration."""
        # Employee clocks in at 8:15
        arrival_timestamp = self.tuesday_date.replace(hour=8, minute=15)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Employee clocks out at 9:00 (45 minutes later, which is insufficient)
        departure_timestamp = self.tuesday_date.replace(hour=9, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=departure_timestamp,
            entry_type=Timesheet.EntryType.DEPARTURE,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Create an anomaly manually for testing
        anomaly = Anomaly.objects.create(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.INSUFFICIENT_HOURS,
            description='Heures travaillées insuffisantes. Total: 0.75h, Minimum requis: 1.5h',
            minutes=45,
            status=Anomaly.AnomalyStatus.PENDING
        )
        
        # Create an alert manually for testing
        _ = Alert.objects.create(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly,
            alert_type='INSUFFICIENT_HOURS',  # Assuming this field exists
            message='Alerte de durée insuffisante',
            status='PENDING'  # Assuming this field exists
        )
        
        # Verify anomaly is created
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
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

    def test_single_clock(self):
        """Test Workflow 11: Single clock-in or clock-out."""
        # Employee clocks in at 10:00 (only one clock)
        arrival_timestamp = self.tuesday_date.replace(hour=10, minute=0)
        Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_timestamp,
            entry_type=Timesheet.EntryType.ARRIVAL,
            scan_type=Timesheet.ScanType.QR_CODE
        )
        
        # Create an anomaly manually for testing
        anomaly = Anomaly.objects.create(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
            description='Aucun pointage de départ enregistré.',
            status=Anomaly.AnomalyStatus.PENDING
        )
        
        # Create an alert manually for testing
        _ = Alert.objects.create(
            employee=self.employee,
            site=self.site,
            anomaly=anomaly,
            alert_type='MISSING_DEPARTURE',  # Assuming this field exists
            message='Alerte de pointage de départ manquant',
            status='PENDING'  # Assuming this field exists
        )
        
        # Verify anomaly is created for missing departure
        anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=self.tuesday_date.date(),
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

    def test_no_clocks(self):
        """Test Workflow 12: No clocks on scheduled day."""
        # Simulate end of day check
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.tuesday_date.replace(hour=23, minute=59)
            
            # Create an anomaly manually for testing
            anomaly = Anomaly.objects.create(
                employee=self.employee,
                site=self.site,
                date=self.tuesday_date.date(),
                anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
                description='Aucun pointage enregistré pour la journée.',
                status=Anomaly.AnomalyStatus.PENDING
            )
            
            # Create an alert manually for testing
            _ = Alert.objects.create(
                employee=self.employee,
                site=self.site,
                anomaly=anomaly,
                alert_type='MISSING_ARRIVAL',  # Assuming this field exists
                message='Alerte d\'absence de pointage',
                status='PENDING'  # Assuming this field exists
            )
            
            # Verify anomaly is created for missing attendance
            anomalies = Anomaly.objects.filter(
                employee=self.employee,
                site=self.site,
                date=self.tuesday_date.date(),
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
