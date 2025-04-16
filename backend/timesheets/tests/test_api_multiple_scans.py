"""
Tests pour vérifier que la détection des scans multiples via l'API suit parfaitement l'arbre de décision
défini dans .cursor/rules/scan_anomalies.mdc
"""
import logging
from datetime import datetime, time, timedelta
from django.test import override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization

User = get_user_model()

# Configurer le logging pour les tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@override_settings(DEBUG=True)
class APIMultipleScansTestCase(APITestCase):
    """Tests pour vérifier que la détection des scans multiples via l'API suit parfaitement l'arbre de décision"""

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

        # Créer un utilisateur admin pour les tests API
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin_password",
            first_name="Admin",
            last_name="User",
            role="ADMIN",
            is_superuser=True
        )

        # Associer l'utilisateur admin à l'organisation
        self.admin_user.organizations.add(self.organization)

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

        # Associer les employés aux plannings et aux organisations
        self.employee_full_day.organizations.add(self.organization)
        self.employee_morning.organizations.add(self.organization)
        self.employee_afternoon.organizations.add(self.organization)
        self.employee_frequency.organizations.add(self.organization)

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

    def test_full_day_multiple_scans_via_api(self):
        """
        Test pour un planning journée complète avec plus de 4 pointages via l'API
        Arbre de décision: Planning fixe -> Journée complète -> Plus de 4 pointages -> Anomalie scan multiple
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_full_day)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer 4 pointages normaux via l'API

        # 1. Arrivée du matin
        arrival_morning_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)
        data_arrival_morning = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_morning_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_arrival_morning = self.client.post('/api/v1/timesheets/create/', data_arrival_morning, format='json')
        self.assertEqual(response_arrival_morning.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée du matin a échoué avec le code {response_arrival_morning.status_code}: {response_arrival_morning.data}")

        # 2. Départ du matin
        departure_morning_dt = timezone.now().astimezone(local_tz).replace(hour=12, minute=0, second=0, microsecond=0)
        data_departure_morning = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_morning_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }
        response_departure_morning = self.client.post('/api/v1/timesheets/create/', data_departure_morning, format='json')
        self.assertEqual(response_departure_morning.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ du matin a échoué avec le code {response_departure_morning.status_code}: {response_departure_morning.data}")

        # 3. Arrivée de l'après-midi
        arrival_afternoon_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)
        data_arrival_afternoon = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_afternoon_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_arrival_afternoon = self.client.post('/api/v1/timesheets/create/', data_arrival_afternoon, format='json')
        self.assertEqual(response_arrival_afternoon.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée de l'après-midi a échoué avec le code {response_arrival_afternoon.status_code}: {response_arrival_afternoon.data}")

        # 4. Départ de l'après-midi
        departure_afternoon_dt = timezone.now().astimezone(local_tz).replace(hour=17, minute=0, second=0, microsecond=0)
        data_departure_afternoon = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_afternoon_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }
        response_departure_afternoon = self.client.post('/api/v1/timesheets/create/', data_departure_afternoon, format='json')
        self.assertEqual(response_departure_afternoon.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ de l'après-midi a échoué avec le code {response_departure_afternoon.status_code}: {response_departure_afternoon.data}")

        # Vérifier qu'aucune anomalie n'a été créée jusqu'à présent
        anomalies_before = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies_before.count(), 0, "Des anomalies ont été créées alors que le nombre de pointages est normal")

        # 5. Créer un 5ème pointage (scan multiple)
        extra_scan_dt = timezone.now().astimezone(local_tz).replace(hour=18, minute=0, second=0, microsecond=0)
        data_extra_scan = {
            'site_id': self.site.nfc_id,
            'timestamp': extra_scan_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_extra_scan = self.client.post('/api/v1/timesheets/create/', data_extra_scan, format='json')
        self.assertEqual(response_extra_scan.status_code, status.HTTP_201_CREATED,
                         f"La requête du scan supplémentaire a échoué avec le code {response_extra_scan.status_code}: {response_extra_scan.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies_after = Anomaly.objects.filter(
            employee=self.employee_full_day,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies_after.count(), 1, "Aucune anomalie de scan multiple n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies_after.first()
        self.assertEqual(anomaly.schedule, self.full_day_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("journée complète", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 5)

    def test_morning_schedule_multiple_scans_via_api(self):
        """
        Test pour un planning demi-journée matin avec plus de 2 pointages via l'API
        Arbre de décision: Planning fixe -> Demi-journée matin -> Plus de 2 pointages -> Anomalie scan multiple
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_morning)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer 2 pointages normaux via l'API

        # 1. Arrivée du matin
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)
        data_arrival = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_arrival = self.client.post('/api/v1/timesheets/create/', data_arrival, format='json')
        self.assertEqual(response_arrival.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {response_arrival.status_code}: {response_arrival.data}")

        # 2. Départ du matin
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=12, minute=0, second=0, microsecond=0)
        data_departure = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }
        response_departure = self.client.post('/api/v1/timesheets/create/', data_departure, format='json')
        self.assertEqual(response_departure.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {response_departure.status_code}: {response_departure.data}")

        # Vérifier qu'aucune anomalie n'a été créée jusqu'à présent
        anomalies_before = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies_before.count(), 0, "Des anomalies ont été créées alors que le nombre de pointages est normal")

        # 3. Créer un 3ème pointage (scan multiple)
        extra_scan_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)
        data_extra_scan = {
            'site_id': self.site.nfc_id,
            'timestamp': extra_scan_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_extra_scan = self.client.post('/api/v1/timesheets/create/', data_extra_scan, format='json')
        self.assertEqual(response_extra_scan.status_code, status.HTTP_201_CREATED,
                         f"La requête du scan supplémentaire a échoué avec le code {response_extra_scan.status_code}: {response_extra_scan.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies_after = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies_after.count(), 1, "Aucune anomalie de scan multiple n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies_after.first()
        self.assertEqual(anomaly.schedule, self.morning_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("demi-journée matin", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_afternoon_schedule_multiple_scans_via_api(self):
        """
        Test pour un planning demi-journée après-midi avec plus de 2 pointages via l'API
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Plus de 2 pointages -> Anomalie scan multiple
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_afternoon)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer 2 pointages normaux via l'API

        # 1. Arrivée de l'après-midi
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)
        data_arrival = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_arrival = self.client.post('/api/v1/timesheets/create/', data_arrival, format='json')
        self.assertEqual(response_arrival.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {response_arrival.status_code}: {response_arrival.data}")

        # 2. Départ de l'après-midi
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=17, minute=0, second=0, microsecond=0)
        data_departure = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }
        response_departure = self.client.post('/api/v1/timesheets/create/', data_departure, format='json')
        self.assertEqual(response_departure.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {response_departure.status_code}: {response_departure.data}")

        # Vérifier qu'aucune anomalie n'a été créée jusqu'à présent
        anomalies_before = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies_before.count(), 0, "Des anomalies ont été créées alors que le nombre de pointages est normal")

        # 3. Créer un 3ème pointage (scan multiple)
        extra_scan_dt = timezone.now().astimezone(local_tz).replace(hour=18, minute=0, second=0, microsecond=0)
        data_extra_scan = {
            'site_id': self.site.nfc_id,
            'timestamp': extra_scan_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_extra_scan = self.client.post('/api/v1/timesheets/create/', data_extra_scan, format='json')
        self.assertEqual(response_extra_scan.status_code, status.HTTP_201_CREATED,
                         f"La requête du scan supplémentaire a échoué avec le code {response_extra_scan.status_code}: {response_extra_scan.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies_after = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies_after.count(), 1, "Aucune anomalie de scan multiple n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies_after.first()
        self.assertEqual(anomaly.schedule, self.afternoon_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("demi-journée après-midi", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)

    def test_frequency_schedule_multiple_scans_via_api(self):
        """
        Test pour un planning fréquence avec plus de 2 pointages via l'API
        Arbre de décision: Planning fréquence -> Plus de 2 pointages -> Anomalie scan multiple
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_frequency)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer 2 pointages normaux via l'API

        # 1. Arrivée
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)
        data_arrival = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_arrival = self.client.post('/api/v1/timesheets/create/', data_arrival, format='json')
        self.assertEqual(response_arrival.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {response_arrival.status_code}: {response_arrival.data}")

        # 2. Départ
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=12, minute=0, second=0, microsecond=0)
        data_departure = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }
        response_departure = self.client.post('/api/v1/timesheets/create/', data_departure, format='json')
        self.assertEqual(response_departure.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {response_departure.status_code}: {response_departure.data}")

        # Vérifier qu'aucune anomalie n'a été créée jusqu'à présent
        anomalies_before = Anomaly.objects.filter(
            employee=self.employee_frequency,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies_before.count(), 0, "Des anomalies ont été créées alors que le nombre de pointages est normal")

        # 3. Créer un 3ème pointage (scan multiple)
        extra_scan_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)
        data_extra_scan = {
            'site_id': self.site.nfc_id,
            'timestamp': extra_scan_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }
        response_extra_scan = self.client.post('/api/v1/timesheets/create/', data_extra_scan, format='json')
        self.assertEqual(response_extra_scan.status_code, status.HTTP_201_CREATED,
                         f"La requête du scan supplémentaire a échoué avec le code {response_extra_scan.status_code}: {response_extra_scan.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies_after = Anomaly.objects.filter(
            employee=self.employee_frequency,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE
        )
        self.assertEqual(anomalies_after.count(), 1, "Aucune anomalie de scan multiple n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies_after.first()
        self.assertEqual(anomaly.schedule, self.frequency_schedule)
        self.assertIn("Scan multiple", anomaly.description)
        self.assertIn("fréquence", anomaly.description)

        # Vérifier que tous les pointages sont associés à l'anomalie
        self.assertEqual(anomaly.related_timesheets.count(), 3)
