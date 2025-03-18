from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from core.models import User, Site, Planning, Pointage, Anomalie, StatistiquesTemps
from core.services import PointageService, EmailService, StatistiquesService
import logging

logger = logging.getLogger(__name__)

class PointageTestCase(TestCase):
    def setUp(self):
        """Configuration initiale des tests"""
        self.gardien = User.objects.create_user(
            username='gardien_test',
            password='test12345',
            role='gardien'
        )
        
        self.site = Site.objects.create(
            name='Site Test',
            qr_code_value='SITE-TEST-001'
        )
        
        # Créer un planning fixe
        self.planning_fixe = Planning.objects.create(
            site=self.site,
            type='FIXE',
            jours_passage='lundi,mardi,mercredi,jeudi,vendredi',
            heure_debut_matin=time(8, 0),
            heure_fin_matin=time(12, 0),
            heure_debut_aprem=time(14, 0),
            heure_fin_aprem=time(18, 0),
            marge_retard=15,
            marge_depart_anticip=15,
            actif=True
        )
        self.planning_fixe.users.add(self.gardien)
        
        # Créer un planning fréquence
        self.planning_frequence = Planning.objects.create(
            site=self.site,
            type='FREQUENCE',
            jours_passage='lundi,mardi,mercredi,jeudi,vendredi',
            duree_prevue_minutes=240,
            marge_duree_pct=10,
            actif=True
        )
        self.planning_frequence.users.add(self.gardien)
        
        # Date de test fixe pour éviter les problèmes de timezone
        self.date_test = timezone.datetime(2025, 1, 21, 8, 0, tzinfo=timezone.get_current_timezone())
        
    def test_pointage_normal(self):
        """Test d'un pointage normal"""
        # Arrivée à l'heure le matin
        pointage = PointageService.creer_pointage(
            user=self.gardien,
            site=self.site,
            date_scan=self.date_test,
            planning=self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage)
        self.assertEqual(pointage.arrivee_ou_depart, 'arrivee')
        self.assertEqual(pointage.periode, 'MATIN')
        
        # Départ normal le matin
        date_depart = self.date_test.replace(hour=12)
        pointage_depart = PointageService.creer_pointage(
            user=self.gardien,
            site=self.site,
            date_scan=date_depart,
            planning=self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage_depart)
        self.assertEqual(pointage_depart.arrivee_ou_depart, 'depart')
        self.assertEqual(pointage_depart.periode, 'MATIN')
        
    def test_retard(self):
        """Test d'un pointage en retard"""
        # Arrivée en retard (30 minutes)
        date_retard = self.date_test.replace(hour=8, minute=30)
        pointage = PointageService.creer_pointage(
            user=self.gardien,
            site=self.site,
            date_scan=date_retard,
            planning=self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage)
        
        # Vérifier qu'une anomalie a été créée
        anomalies = Anomalie.objects.filter(
            user=self.gardien,
            site=self.site,
            type_anomalie='retard'
        )
        self.assertTrue(anomalies.exists())
        
    def test_depart_anticipe(self):
        """Test d'un départ anticipé"""
        # Arrivée normale
        pointage_arrivee = PointageService.creer_pointage(
            user=self.gardien,
            site=self.site,
            date_scan=self.date_test,
            planning=self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage_arrivee)
        
        # Départ anticipé (30 minutes)
        date_depart = self.date_test.replace(hour=11, minute=30)
        pointage_depart = PointageService.creer_pointage(
            user=self.gardien,
            site=self.site,
            date_scan=date_depart,
            planning=self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage_depart)
        
        # Vérifier qu'une anomalie a été créée
        anomalies = Anomalie.objects.filter(
            user=self.gardien,
            site=self.site,
            type_anomalie='depart_anticipe'
        )
        self.assertTrue(anomalies.exists())

    def test_pointage_frequence_normal(self):
        """Test des pointages pour un planning FREQUENCE"""
        logger.info("Test des pointages (Planning FREQUENCE)")
        
        # Premier pointage (arrivée)
        date_arrivee = self.date_test.replace(hour=9, minute=0)
        pointage1 = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_arrivee,
            self.planning_frequence,
            periode='matin'
        )
        self.assertEqual(pointage1.arrivee_ou_depart, 'arrivee')
        
        # Deuxième pointage après la durée prévue (départ)
        date_depart = date_arrivee + timedelta(minutes=240)  # Durée exacte
        pointage2 = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_depart,
            self.planning_frequence,
            periode='matin'
        )
        self.assertEqual(pointage2.arrivee_ou_depart, 'depart')
        self.assertEqual(Anomalie.objects.filter(type_anomalie='presence_partielle').count(), 0)
        
    def test_pointage_frequence_duree_insuffisante(self):
        """Test des durées insuffisantes pour un planning FREQUENCE"""
        logger.info("Test des durées insuffisantes (Planning FREQUENCE)")
        
        # Premier pointage (arrivée)
        date_arrivee = self.date_test.replace(hour=9, minute=0)
        pointage1 = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_arrivee,
            self.planning_frequence,
            periode='matin'
        )
        
        # Deuxième pointage avant la durée minimale (départ)
        date_depart = date_arrivee + timedelta(minutes=100)  # 20 minutes de moins
        pointage2 = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_depart,
            self.planning_frequence,
            periode='matin'
        )
        
        # Vérification de la création d'anomalie
        self.assertEqual(Anomalie.objects.filter(type_anomalie='presence_partielle').count(), 1)
        
    def test_batch_verification(self):
        """Test du batch de vérification à 22h"""
        logger.info("Test du batch de vérification")
        
        # Test pour planning FIXE sans pointages
        PointageService.verifier_plannings_fixe()
        self.assertTrue(Anomalie.objects.filter(type_anomalie='absence_totale').exists())
        
        # Test pour planning FREQUENCE sans pointages
        PointageService.verifier_plannings_frequence()
        self.assertTrue(Anomalie.objects.filter(type_anomalie='absence_totale').exists())
        
    def test_statistiques(self):
        """Test de la mise à jour des statistiques"""
        logger.info("Test des statistiques")
        
        # Création d'un pointage avec retard
        date_retard = self.date_test.replace(hour=8, minute=30)  # 30 minutes de retard
        pointage = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_retard,
            self.planning_fixe,
            periode='matin'
        )
        
        # Vérification des statistiques
        stats = StatistiquesTemps.objects.get(
            user=self.gardien,
            site=self.site,
            mois=self.date_test.month,
            annee=self.date_test.year
        )
        self.assertEqual(stats.minutes_manquantes_total, 30)

    def test_association_utilisateur_planning(self):
        """Test des associations utilisateur-planning"""
        logger.info("Test des associations utilisateur-planning")
        
        # Vérifier que l'utilisateur est bien associé
        self.assertTrue(self.planning_fixe.users.filter(id=self.gardien.id).exists())
        
        # Vérifier qu'un pointage est possible avec cette association
        date_pointage = self.date_test.replace(hour=8, minute=0)
        pointage = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_pointage,
            self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage)
        
    def test_gestion_anomalies_avancee(self):
        """Test approfondi de la gestion des anomalies"""
        logger.info("Test de la gestion avancée des anomalies")
        
        # Test d'accumulation d'anomalies sur une journée
        # Retard le matin
        date_retard_matin = self.date_test.replace(hour=8, minute=30)
        pointage_matin = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_retard_matin,
            self.planning_fixe,
            periode='MATIN'
        )
        
        # Départ anticipé l'après-midi
        date_depart_aprem = self.date_test.replace(hour=17, minute=30)
        pointage_aprem = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_depart_aprem,
            self.planning_fixe,
            periode='APRES_MIDI'
        )
        
        # Vérifier le nombre total d'anomalies
        nb_anomalies = Anomalie.objects.filter(
            user=self.gardien,
            site=self.site,
            date_declaration__date=self.date_test.date()
        ).count()
        self.assertEqual(nb_anomalies, 2)  # Une pour le retard, une pour le départ anticipé

    def test_statistiques_avancees(self):
        """Test approfondi des statistiques de temps"""
        logger.info("Test des statistiques avancées")
        
        # Créer plusieurs pointages sur différents jours
        dates_test = [
            self.date_test,  # Jour 1
            self.date_test + timedelta(days=1),  # Jour 2
            self.date_test + timedelta(days=2)   # Jour 3
        ]
        
        for date in dates_test:
            # Pointage avec retard le matin
            date_retard = date.replace(hour=8, minute=20)
            PointageService.creer_pointage(
                self.gardien,
                self.site,
                date_retard,
                self.planning_fixe,
                periode='MATIN'
            )
            
            # Pointage avec départ anticipé l'après-midi
            date_depart = date.replace(hour=17, minute=40)
            PointageService.creer_pointage(
                self.gardien,
                self.site,
                date_depart,
                self.planning_fixe,
                periode='APRES_MIDI'
            )
        
        # Vérifier les statistiques cumulées
        stats = StatistiquesTemps.objects.get(
            user=self.gardien,
            site=self.site,
            mois=self.date_test.month,
            annee=self.date_test.year
        )
        
        # 20 minutes de retard + 20 minutes de départ anticipé = 40 minutes par jour
        # Sur 3 jours = 120 minutes
        self.assertEqual(stats.minutes_manquantes_total, 120)

    def test_cas_limites(self):
        """Test des cas limites et des erreurs"""
        logger.info("Test des cas limites")
        
        # Test de pointage à minuit
        date_minuit = self.date_test.replace(hour=0, minute=0)
        pointage_minuit = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_minuit,
            self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage_minuit)
        
        # Test de pointage à 23h59
        date_23h59 = self.date_test.replace(hour=23, minute=59)
        pointage_23h59 = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_23h59,
            self.planning_fixe,
            periode='APRES_MIDI'
        )
        self.assertIsNotNone(pointage_23h59)
        
        # Test de pointage pendant la pause déjeuner
        date_pause = self.date_test.replace(hour=13, minute=0)
        pointage_pause = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_pause,
            self.planning_fixe,
            periode='MATIN'  # On force la période matin pour voir le comportement
        )
        self.assertIsNotNone(pointage_pause)

    def test_validations_et_erreurs(self):
        """Test des validations et de la gestion des erreurs"""
        logger.info("Test des validations et erreurs")
        
        # Test avec une date dans le futur
        date_future = timezone.now() + timedelta(days=1)
        pointage_futur = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_future,
            self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage_futur)
        
        # Test de la cohérence des pointages
        # Premier pointage (arrivée)
        PointageService.creer_pointage(
            self.gardien,
            self.site,
            self.date_test.replace(hour=8, minute=0),
            self.planning_fixe,
            periode='MATIN'
        )
        
        # Deuxième pointage (départ) immédiatement après
        pointage_coherence = PointageService.creer_pointage(
            self.gardien,
            self.site,
            self.date_test.replace(hour=8, minute=1),
            self.planning_fixe,
            periode='MATIN'
        )
        self.assertIsNotNone(pointage_coherence)
        
        # Vérifier qu'une anomalie a été créée pour le pointage trop rapproché
        anomalie_coherence = Anomalie.objects.filter(
            user=self.gardien,
            site=self.site,
            type_anomalie='coherence'
        ).exists()
        self.assertTrue(anomalie_coherence)

    def test_nettoyage_double_pointages(self):
        """Test du nettoyage des double-pointages"""
        logger.info("Test du nettoyage des double-pointages")
        
        # Créer un premier pointage
        date_test = self.date_test.replace(hour=8, minute=0)
        premier_pointage = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_test,
            self.planning_fixe,
            periode='MATIN'
        )
        
        # Créer un deuxième pointage à la même minute
        deuxieme_pointage = PointageService.creer_pointage(
            self.gardien,
            self.site,
            date_test,
            self.planning_fixe,
            periode='MATIN'
        )
        
        # Vérifier qu'un seul pointage existe
        nb_pointages = Pointage.objects.filter(
            user=self.gardien,
            site=self.site,
            date_scan__date=date_test.date(),
            periode='MATIN'
        ).count()
        self.assertEqual(nb_pointages, 1) 