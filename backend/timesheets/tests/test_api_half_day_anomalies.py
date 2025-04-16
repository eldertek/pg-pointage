"""
Tests pour vérifier que la détection d'anomalies pour les plannings demi-journée
suit parfaitement l'arbre de décision défini dans .cursor/rules/scan_anomalies.mdc
en utilisant l'API comme le ferait un utilisateur réel
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
class APIHalfDayAnomaliesTestCase(APITestCase):
    """Tests pour vérifier la détection d'anomalies via l'API pour les plannings demi-journée"""

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

        # Associer les employés aux plannings et aux organisations
        self.employee_morning.organizations.add(self.organization)
        self.employee_afternoon.organizations.add(self.organization)

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

        # Créer les détails des plannings pour aujourd'hui
        self.today = timezone.now().date()
        self.today_weekday = self.today.weekday()

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

        # Authentifier l'utilisateur pour les tests API
        self.client.force_authenticate(user=self.admin_user)

    def test_morning_late_arrival_via_api(self):
        """
        Test pour un planning demi-journée matin avec arrivée en retard via l'API
        Arbre de décision: Planning fixe -> Demi-journée matin -> Arrivée en retard -> Anomalie de retard
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé du matin pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_morning)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        local_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=30, second=0, microsecond=0)

        # Préparer les données pour la requête API (comme le ferait l'application mobile)
        data = {
            'site_id': self.site.nfc_id,  # L'ID NFC/QR du site
            'timestamp': local_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête à l'API pour créer un pointage
        response = self.client.post('/api/v1/timesheets/create/', data, format='json')

        # Vérifier que la requête a réussi
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         f"La requête API a échoué avec le code {response.status_code}: {response.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.LATE
        )
        self.assertEqual(anomalies.count(), 1, "Aucune anomalie de retard n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.morning_schedule)
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(anomaly.minutes, 15)
        self.assertIn("matin", anomaly.description)

    def test_morning_early_departure_via_api(self):
        """
        Test pour un planning demi-journée matin avec départ anticipé via l'API
        Arbre de décision: Planning fixe -> Demi-journée matin -> Départ anticipé -> Anomalie de départ anticipé
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé du matin pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_morning)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer un pointage d'arrivée à l'heure via l'API
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)
        arrival_data = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour l'arrivée
        arrival_response = self.client.post('/api/v1/timesheets/create/', arrival_data, format='json')
        self.assertEqual(arrival_response.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {arrival_response.status_code}: {arrival_response.data}")

        # Créer un pointage de départ anticipé (30 minutes avant l'heure prévue) via l'API
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=11, minute=30, second=0, microsecond=0)
        departure_data = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour le départ
        departure_response = self.client.post('/api/v1/timesheets/create/', departure_data, format='json')
        self.assertEqual(departure_response.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {departure_response.status_code}: {departure_response.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1, "Aucune anomalie de départ anticipé n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.morning_schedule)
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(anomaly.minutes, 15)
        self.assertIn("matin", anomaly.description)

    def test_afternoon_late_arrival_via_api(self):
        """
        Test pour un planning demi-journée après-midi avec arrivée en retard via l'API
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Arrivée en retard -> Anomalie de retard
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé de l'après-midi pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_afternoon)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        local_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=30, second=0, microsecond=0)

        # Préparer les données pour la requête API
        data = {
            'site_id': self.site.nfc_id,
            'timestamp': local_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête à l'API pour créer un pointage
        response = self.client.post('/api/v1/timesheets/create/', data, format='json')

        # Vérifier que la requête a réussi
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         f"La requête API a échoué avec le code {response.status_code}: {response.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.LATE
        )
        self.assertEqual(anomalies.count(), 1, "Aucune anomalie de retard n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.afternoon_schedule)
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(anomaly.minutes, 15)
        self.assertIn("après-midi", anomaly.description)

    def test_afternoon_early_departure_via_api(self):
        """
        Test pour un planning demi-journée après-midi avec départ anticipé via l'API
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Départ anticipé -> Anomalie de départ anticipé
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé de l'après-midi pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_afternoon)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer un pointage d'arrivée à l'heure via l'API
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)
        arrival_data = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour l'arrivée
        arrival_response = self.client.post('/api/v1/timesheets/create/', arrival_data, format='json')
        self.assertEqual(arrival_response.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {arrival_response.status_code}: {arrival_response.data}")

        # Créer un pointage de départ anticipé (30 minutes avant l'heure prévue) via l'API
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=16, minute=30, second=0, microsecond=0)
        departure_data = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour le départ
        departure_response = self.client.post('/api/v1/timesheets/create/', departure_data, format='json')
        self.assertEqual(departure_response.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {departure_response.status_code}: {departure_response.data}")

        # Vérifier qu'une anomalie a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.EARLY_DEPARTURE
        )
        self.assertEqual(anomalies.count(), 1, "Aucune anomalie de départ anticipé n'a été créée")

        # Vérifier les détails de l'anomalie
        anomaly = anomalies.first()
        self.assertEqual(anomaly.schedule, self.afternoon_schedule)
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(anomaly.minutes, 15)
        self.assertIn("après-midi", anomaly.description)

    def test_morning_on_time_no_anomaly_via_api(self):
        """
        Test pour un planning demi-journée matin avec pointages à l'heure via l'API (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Demi-journée matin -> Pointages à l'heure -> Pas d'anomalie
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé du matin pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_morning)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer un pointage d'arrivée à l'heure via l'API
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)
        arrival_data = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour l'arrivée
        arrival_response = self.client.post('/api/v1/timesheets/create/', arrival_data, format='json')
        self.assertEqual(arrival_response.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {arrival_response.status_code}: {arrival_response.data}")

        # Créer un pointage de départ à l'heure via l'API
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=12, minute=0, second=0, microsecond=0)
        departure_data = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour le départ
        departure_response = self.client.post('/api/v1/timesheets/create/', departure_data, format='json')
        self.assertEqual(departure_response.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {departure_response.status_code}: {departure_response.data}")

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 0, "Des anomalies ont été créées alors que les pointages sont à l'heure")

    def test_morning_within_margin_no_anomaly_via_api(self):
        """
        Test pour un planning demi-journée matin avec pointages dans la marge de tolérance via l'API (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Demi-journée matin -> Pointages dans la marge -> Pas d'anomalie
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Authentifier l'employé du matin pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_morning)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer un pointage d'arrivée dans la marge de tolérance (10 minutes de retard, marge = 15) via l'API
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=10, second=0, microsecond=0)
        arrival_data = {
            'site_id': self.site.nfc_id,
            'timestamp': arrival_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour l'arrivée
        arrival_response = self.client.post('/api/v1/timesheets/create/', arrival_data, format='json')
        self.assertEqual(arrival_response.status_code, status.HTTP_201_CREATED,
                         f"La requête d'arrivée a échoué avec le code {arrival_response.status_code}: {arrival_response.data}")

        # Créer un pointage de départ dans la marge de tolérance (10 minutes avant, marge = 15) via l'API
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=11, minute=50, second=0, microsecond=0)
        departure_data = {
            'site_id': self.site.nfc_id,
            'timestamp': departure_dt.isoformat(),
            'entry_type': 'DEPARTURE',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête pour le départ
        departure_response = self.client.post('/api/v1/timesheets/create/', departure_data, format='json')
        self.assertEqual(departure_response.status_code, status.HTTP_201_CREATED,
                         f"La requête de départ a échoué avec le code {departure_response.status_code}: {departure_response.data}")

        # Vérifier qu'aucune anomalie n'a été créée
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 0, "Des anomalies ont été créées alors que les pointages sont dans la marge de tolérance")

    def test_update_missing_arrival_to_late_via_api(self):
        """
        Test pour la mise à jour d'une anomalie d'arrivée manquante en retard via l'API
        Arbre de décision: Planning fixe -> Demi-journée matin -> Anomalie existante -> Mise à jour
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Créer une anomalie d'arrivée manquante
        missing_arrival = Anomaly.objects.create(
            employee=self.employee_morning,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.MISSING_ARRIVAL,
            description="Arrivée manquante selon le planning",
            status=Anomaly.AnomalyStatus.PENDING,
            schedule=self.morning_schedule
        )

        # Authentifier l'employé du matin pour simuler un scan réel
        self.client.force_authenticate(user=self.employee_morning)

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        local_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=30, second=0, microsecond=0)

        # Préparer les données pour la requête API
        data = {
            'site_id': self.site.nfc_id,
            'timestamp': local_dt.isoformat(),
            'entry_type': 'ARRIVAL',
            'scan_type': 'QR_CODE'
        }

        # Envoyer la requête à l'API pour créer un pointage
        response = self.client.post('/api/v1/timesheets/create/', data, format='json')

        # Vérifier que la requête a réussi
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         f"La requête API a échoué avec le code {response.status_code}: {response.data}")

        # Vérifier qu'il n'y a toujours qu'une seule anomalie
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 1, "L'anomalie n'a pas été mise à jour correctement")

        # Vérifier les détails de l'anomalie mise à jour
        updated_anomaly = anomalies.first()
        self.assertEqual(updated_anomaly.id, missing_arrival.id, "L'ID de l'anomalie a changé, ce n'est pas une mise à jour")
        self.assertEqual(updated_anomaly.anomaly_type, Anomaly.AnomalyType.LATE, "Le type d'anomalie n'a pas été mis à jour")
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(updated_anomaly.minutes, 15, "Les minutes de retard ne sont pas correctes")
        self.assertIn("matin", updated_anomaly.description, "La description ne mentionne pas le matin")
