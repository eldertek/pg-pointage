"""
Tests pour vérifier que la détection d'anomalies pour les plannings demi-journée
suit parfaitement l'arbre de décision défini dans .cursor/rules/scan_anomalies.mdc
"""
import logging
from datetime import datetime, time, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from timesheets.models import Timesheet, Anomaly
from sites.models import Site, Schedule, ScheduleDetail, SiteEmployee
from organizations.models import Organization
from timesheets.utils.anomaly_processor import AnomalyProcessor

User = get_user_model()

# Configurer le logging pour les tests
logging.basicConfig(level=logging.DEBUG)

@override_settings(DEBUG=True)
class HalfDayAnomaliesDecisionTreeTestCase(TestCase):
    """Tests pour vérifier que la détection d'anomalies pour les plannings demi-journée suit parfaitement l'arbre de décision"""

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

        # Associer les employés aux plannings
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

        # Initialiser le processeur d'anomalies
        self.anomaly_processor = AnomalyProcessor()

    def test_morning_late_arrival(self):
        """
        Test pour un planning demi-journée matin avec arrivée en retard
        Arbre de décision: Planning fixe -> Demi-journée matin -> Arrivée en retard -> Anomalie de retard
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Créer un pointage d'arrivée en retard (30 minutes après l'heure prévue)
        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        local_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=30, second=0, microsecond=0)

        timesheet = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=local_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage (le signal post_save crée déjà l'anomalie)
        self.anomaly_processor.process_timesheet(timesheet)

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

    def test_morning_early_departure(self):
        """
        Test pour un planning demi-journée matin avec départ anticipé
        Arbre de décision: Planning fixe -> Demi-journée matin -> Départ anticipé -> Anomalie de départ anticipé
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer un pointage d'arrivée à l'heure
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)
        Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ anticipé (30 minutes avant l'heure prévue)
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=11, minute=30, second=0, microsecond=0)
        timesheet = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage (le signal post_save crée déjà l'anomalie)
        self.anomaly_processor.process_timesheet(timesheet)

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

    def test_afternoon_late_arrival(self):
        """
        Test pour un planning demi-journée après-midi avec arrivée en retard
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Arrivée en retard -> Anomalie de retard
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        local_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=30, second=0, microsecond=0)

        # Créer un pointage d'arrivée en retard (30 minutes après l'heure prévue)
        timesheet = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=local_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage (le signal post_save crée déjà l'anomalie)
        self.anomaly_processor.process_timesheet(timesheet)

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

    def test_afternoon_early_departure(self):
        """
        Test pour un planning demi-journée après-midi avec départ anticipé
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Départ anticipé -> Anomalie de départ anticipé
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()

        # Créer un pointage d'arrivée à l'heure
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)
        Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer un pointage de départ anticipé (30 minutes avant l'heure prévue)
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=16, minute=30, second=0, microsecond=0)
        timesheet = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage (le signal post_save crée déjà l'anomalie)
        self.anomaly_processor.process_timesheet(timesheet)

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

    def test_morning_on_time_no_anomaly(self):
        """
        Test pour un planning demi-journée matin avec pointages à l'heure (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Demi-journée matin -> Pointages à l'heure -> Pas d'anomalie
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=0, second=0, microsecond=0)

        # Créer un pointage d'arrivée à l'heure
        arrival = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage d'arrivée
        self.anomaly_processor.process_timesheet(arrival)

        # Créer un pointage de départ à l'heure
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=12, minute=0, second=0, microsecond=0)
        departure = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage de départ
        self.anomaly_processor.process_timesheet(departure)

        # Vérifier qu'aucune anomalie n'existe pour cet employé aujourd'hui
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 0, "Des anomalies ont été créées alors que les pointages sont à l'heure")

    def test_afternoon_on_time_no_anomaly(self):
        """
        Test pour un planning demi-journée après-midi avec pointages à l'heure (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Pointages à l'heure -> Pas d'anomalie
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)

        # Créer un pointage d'arrivée à l'heure
        arrival = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage d'arrivée
        self.anomaly_processor.process_timesheet(arrival)

        # Créer un pointage de départ à l'heure
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=17, minute=0, second=0, microsecond=0)
        departure = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage de départ
        self.anomaly_processor.process_timesheet(departure)

        # Vérifier qu'aucune anomalie n'existe pour cet employé aujourd'hui
        anomalies = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 0, "Des anomalies ont été créées alors que les pointages sont à l'heure")

    def test_morning_within_margin_no_anomaly(self):
        """
        Test pour un planning demi-journée matin avec pointages dans la marge de tolérance (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Demi-journée matin -> Pointages dans la marge -> Pas d'anomalie
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=10, second=0, microsecond=0)

        # Créer un pointage d'arrivée dans la marge de tolérance (10 minutes de retard, marge = 15)
        arrival = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage d'arrivée
        self.anomaly_processor.process_timesheet(arrival)

        # Créer un pointage de départ dans la marge de tolérance (10 minutes avant, marge = 15)
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=11, minute=50, second=0, microsecond=0)
        departure = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage de départ
        self.anomaly_processor.process_timesheet(departure)

        # Vérifier qu'aucune anomalie n'existe pour cet employé aujourd'hui
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 0, "Des anomalies ont été créées alors que les pointages sont dans la marge de tolérance")

    def test_afternoon_within_margin_no_anomaly(self):
        """
        Test pour un planning demi-journée après-midi avec pointages dans la marge de tolérance (aucune anomalie ne doit être créée)
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Pointages dans la marge -> Pas d'anomalie
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=10, second=0, microsecond=0)

        # Créer un pointage d'arrivée dans la marge de tolérance (10 minutes de retard, marge = 15)
        arrival = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage d'arrivée
        self.anomaly_processor.process_timesheet(arrival)

        # Créer un pointage de départ dans la marge de tolérance (10 minutes avant, marge = 15)
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=16, minute=50, second=0, microsecond=0)
        departure = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage de départ
        self.anomaly_processor.process_timesheet(departure)

        # Vérifier qu'aucune anomalie n'existe pour cet employé aujourd'hui
        anomalies = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 0, "Des anomalies ont été créées alors que les pointages sont dans la marge de tolérance")

    def test_morning_update_missing_arrival_to_late(self):
        """
        Test pour la mise à jour d'une anomalie d'arrivée manquante en retard pour un planning demi-journée matin
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

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        local_dt = timezone.now().astimezone(local_tz).replace(hour=8, minute=30, second=0, microsecond=0)

        # Créer un pointage d'arrivée en retard
        timesheet = Timesheet.objects.create(
            employee=self.employee_morning,
            site=self.site,
            timestamp=local_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Traiter le pointage (le signal post_save met à jour l'anomalie)
        self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'il n'y a toujours qu'une seule anomalie
        anomalies = Anomaly.objects.filter(
            employee=self.employee_morning,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 1, "L'anomalie n'a pas été mise à jour correctement")

        # Vérifier les détails de l'anomalie mise à jour
        updated_anomaly = anomalies.first()
        self.assertEqual(updated_anomaly.id, missing_arrival.id, "L'ID de l'anomalie a changé, ce n'est pas une mise à jour")  # Même ID = même anomalie
        self.assertEqual(updated_anomaly.anomaly_type, Anomaly.AnomalyType.LATE, "Le type d'anomalie n'a pas été mis à jour")
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(updated_anomaly.minutes, 15, "Les minutes de retard ne sont pas correctes")
        self.assertIn("matin", updated_anomaly.description, "La description ne mentionne pas le matin")

    def test_afternoon_update_missing_departure_to_early_departure(self):
        """
        Test pour la mise à jour d'une anomalie de départ manquant en départ anticipé pour un planning demi-journée après-midi
        Arbre de décision: Planning fixe -> Demi-journée après-midi -> Anomalie existante -> Mise à jour
        """
        # Supprimer toutes les anomalies existantes
        Anomaly.objects.all().delete()

        # Utiliser un timestamp avec le fuseau horaire local pour éviter les problèmes de conversion
        local_tz = timezone.get_current_timezone()
        arrival_dt = timezone.now().astimezone(local_tz).replace(hour=13, minute=0, second=0, microsecond=0)

        # Créer un pointage d'arrivée
        Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=arrival_dt,
            entry_type=Timesheet.EntryType.ARRIVAL
        )

        # Créer une anomalie de départ manquant
        missing_departure = Anomaly.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today,
            anomaly_type=Anomaly.AnomalyType.MISSING_DEPARTURE,
            description="Départ manquant selon le planning",
            status=Anomaly.AnomalyStatus.PENDING,
            schedule=self.afternoon_schedule
        )

        # Créer un pointage de départ anticipé
        departure_dt = timezone.now().astimezone(local_tz).replace(hour=16, minute=30, second=0, microsecond=0)
        timesheet = Timesheet.objects.create(
            employee=self.employee_afternoon,
            site=self.site,
            timestamp=departure_dt,
            entry_type=Timesheet.EntryType.DEPARTURE
        )

        # Traiter le pointage (le signal post_save met à jour l'anomalie)
        self.anomaly_processor.process_timesheet(timesheet)

        # Vérifier qu'il n'y a toujours qu'une seule anomalie
        anomalies = Anomaly.objects.filter(
            employee=self.employee_afternoon,
            site=self.site,
            date=self.today
        )
        self.assertEqual(anomalies.count(), 1, "L'anomalie n'a pas été mise à jour correctement")

        # Vérifier les détails de l'anomalie mise à jour
        updated_anomaly = anomalies.first()
        self.assertEqual(updated_anomaly.id, missing_departure.id, "L'ID de l'anomalie a changé, ce n'est pas une mise à jour")  # Même ID = même anomalie
        self.assertEqual(updated_anomaly.anomaly_type, Anomaly.AnomalyType.EARLY_DEPARTURE, "Le type d'anomalie n'a pas été mis à jour")
        # Vérifier que les minutes sont supérieures à la marge de tolérance (15 minutes)
        self.assertGreater(updated_anomaly.minutes, 15, "Les minutes de départ anticipé ne sont pas correctes")
        self.assertIn("après-midi", updated_anomaly.description, "La description ne mentionne pas l'après-midi")
