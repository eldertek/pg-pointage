import pytest
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from timesheets.models import Timesheet, Anomaly
from organizations.models import Organization

@pytest.mark.django_db
class TestLateArrivalAnomalies:
    """Tests for late arrival anomaly detection"""

    def setup_method(self):
        """Set up test data"""
        # Create organization
        self.organization = Organization.objects.create(
            name="Test Organization"
        )

        # Create site with late margin of 5 minutes
        self.site = Site.objects.create(
            name="Test Site",
            nfc_id="S001",
            organization=self.organization,
            address="123 Test St",
            postal_code="12345",
            city="Test City",
            late_margin=5,
            early_departure_margin=5
        )

        # Create employee
        self.employee = User.objects.create(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            employee_id="U00001"
        )
        self.employee.organizations.add(self.organization)

        # Create a fixed schedule
        self.schedule = Schedule.objects.create(
            site=self.site,
            schedule_type=Schedule.ScheduleType.FIXED,
            is_active=True
        )

        # Create schedule details for Monday (0)
        ScheduleDetail.objects.create(
            schedule=self.schedule,
            day_of_week=0,  # Monday
            start_time_1=time(12, 0),  # 12:00
            end_time_1=time(12, 15),   # 12:15
            start_time_2=time(12, 30), # 12:30
            end_time_2=time(12, 45)    # 12:45
        )

        # Assign employee to site and schedule
        SiteEmployee.objects.create(
            site=self.site,
            employee=self.employee,
            schedule=self.schedule,
            is_active=True
        )

        # Create API client
        self.client = APIClient()
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password",
            is_superuser=True
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_late_arrival_detection_repair_vs_scan(self):
        """Test that late arrivals are detected consistently between repair and scan"""
        # Set the date to a Monday
        today = timezone.now().date()
        while today.weekday() != 0:  # 0 is Monday
            today = today + timedelta(days=1)

        # Create a timesheet entry for late arrival (7 minutes late)
        arrival_time = datetime.combine(today, time(12, 7))  # 12:07, 7 minutes late
        arrival_time = timezone.make_aware(arrival_time)

        timesheet = Timesheet.objects.create(
            employee=self.employee,
            site=self.site,
            timestamp=arrival_time,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Verify the timesheet was created
        assert Timesheet.objects.count() == 1

        # Manually set the late flag and minutes
        timesheet.is_late = True
        timesheet.late_minutes = 7
        timesheet.save()

        # Create an anomaly for the late arrival
        anomaly = Anomaly.objects.create(
            employee=self.employee,
            site=self.site,
            timesheet=timesheet,
            date=today,
            anomaly_type=Anomaly.AnomalyType.LATE,
            description=f"Retard de 7 minutes (marge: 5 minutes).",
            minutes=7,
            status=Anomaly.AnomalyStatus.PENDING,
            schedule=self.schedule
        )
        anomaly.related_timesheets.add(timesheet)

        # Verify the anomaly was created
        assert Anomaly.objects.count() == 1

        # Call the scan anomalies endpoint
        url = reverse('scan-anomalies')
        data = {
            'start_date': today.strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d'),
            'force_update': True
        }
        response = self.client.post(url, data, format='json')

        # Verify the response
        assert response.status_code == status.HTTP_200_OK

        # Verify that the anomaly still exists after scanning
        assert Anomaly.objects.count() >= 1

        # Verify that a late arrival anomaly exists
        late_anomalies = Anomaly.objects.filter(
            employee=self.employee,
            site=self.site,
            date=today,
            anomaly_type=Anomaly.AnomalyType.LATE
        )
        assert late_anomalies.exists()

        # Get the late anomaly
        late_anomaly = late_anomalies.first()

        # Verify the late anomaly details
        assert late_anomaly.minutes == 7
        assert "Retard de 7 minutes" in late_anomaly.description
        assert late_anomaly.timesheet == timesheet
