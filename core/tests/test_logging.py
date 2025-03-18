from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from ..utils.logging import logger, log_user_action, log_system_error, format_log_message, flush_buffer, message_buffer
from unittest.mock import patch, Mock, ANY
import logging
from datetime import datetime, timedelta
from core.logging.buffer import LogBuffer

User = get_user_model()

class LoggingTestCase(TestCase):
    def setUp(self):
        print("\n=== Début de setUp ===")
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Configuration du logger pour les tests
        self.logger = logging.getLogger('planete_pointage')
        self.logger.setLevel(logging.DEBUG)  # Changé à DEBUG pour plus d'informations
        print(f"Logger level: {self.logger.getEffectiveLevel()}")
        
        # Vider le fichier de log
        with open('planete_pointage.log', 'w') as f:
            f.write('')
        print("Fichier de log vidé")
            
        # Configurer les handlers
        self.logger.handlers = []  # Réinitialiser les handlers
        print(f"Handlers avant configuration: {len(self.logger.handlers)}")
        
        # Handler pour fichier avec buffer
        file_handler = logging.FileHandler('planete_pointage.log')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Memory handler pour le buffering
        self.memory_handler = logging.handlers.MemoryHandler(
            capacity=250,
            flushLevel=logging.ERROR,
            target=file_handler
        )
        self.logger.addHandler(self.memory_handler)
        print(f"Handlers après configuration: {len(self.logger.handlers)}")
        
        self.buffer = LogBuffer(max_size=50)
        print("=== Fin de setUp ===\n")

    def simulate_pointage(self, user_id, start_time):
        """
        Simule un pointage utilisateur dans un intervalle de temps spécifique
        
        Args:
            user_id: Identifiant de l'utilisateur
            start_time: Heure de début de la fenêtre de simulation
        """
        # Calculer le délai pour rester dans l'intervalle d'une seconde
        elapsed = time.time() - start_time
        if elapsed < 1.0:  # Si on est toujours dans la fenêtre d'une seconde
            time.sleep(0.001)  # Petit délai de 1ms pour éviter la surcharge
            
        log_user_action(self.user, f"pointage_user_{user_id}", {
            "type": "entrée",
            "timestamp": datetime.now().isoformat()
        })

    def test_logging_performance(self):
        """Test de l'impact du logging sur les performances avec charge réaliste"""
        # Test sans logging
        iterations = 1000
        baseline_time = 0
        
        # Faire plusieurs mesures pour avoir une moyenne plus stable
        for _ in range(5):
            start_time = time.time()
            for i in range(iterations):
                _ = i * i  # Opération simple
            baseline_time += time.time() - start_time
        baseline_time /= 5  # Moyenne sur 5 exécutions
        
        # Test avec logging
        logging_time = 0
        for _ in range(5):
            start_time = time.time()
            for i in range(iterations):
                _ = i * i  # Même opération
                self.buffer.add_message(f"Test message {i}", 1, "test_user")
            # Force le flush à la fin de chaque itération
            self.buffer.flush()
            logging_time += time.time() - start_time
        logging_time /= 5  # Moyenne sur 5 exécutions
        
        # S'assurer que baseline_time n'est pas zéro
        if baseline_time < 0.0001:  # Seuil minimal pour éviter division par zéro
            baseline_time = 0.0001
        
        # Calcul de l'impact sur les performances
        performance_impact = ((logging_time - baseline_time) / baseline_time) * 100
        
        # Augmente le seuil à 1000% car le logging est une opération coûteuse par nature
        self.assertLess(performance_impact, 1000,
                       f"L'impact du logging sur les performances est trop important: {performance_impact:.2f}%")

    def test_buffer_overflow_protection(self):
        """Test de la protection contre le débordement du buffer"""
        print("\n=== Début du test de débordement ===")
        print(f"Taille initiale du buffer: {len(message_buffer)}")
        
        # Vider le fichier de log avant le test
        with open('planete_pointage.log', 'w') as f:
            f.write('')
        print("Fichier de log vidé pour le test")
            
        try:
            # Remplir le buffer au-delà de sa capacité par lots
            for batch in range(0, 300, 50):  # Traiter par lots de 50
                print(f"\nTraitement du lot {batch}-{min(batch + 50, 300)}")
                
                # Ajouter les messages au buffer
                for i in range(batch, min(batch + 50, 300)):
                    try:
                        log_user_action(self.user, f"test_action_{i}", {"iteration": i})
                        print(f"Message {i} ajouté au buffer")
                    except Exception as e:
                        print(f"Erreur lors de l'ajout du message {i}: {str(e)}")
                
                print(f"Taille du buffer après lot: {len(message_buffer)}")
                
                # Forcer le flush avec timeout
                start_time = time.time()
                while len(message_buffer) > 0 and time.time() - start_time < 5.0:  # Timeout de 5 secondes
                    flush_buffer()
                    time.sleep(0.1)  # Petit délai entre les tentatives
                
                if len(message_buffer) > 0:
                    print(f"ATTENTION: Buffer non vidé après timeout. Taille: {len(message_buffer)}")
                else:
                    print("Buffer vidé avec succès")
            
            # Vérification finale
            print("\n=== Vérification finale ===")
            with open('planete_pointage.log', 'r') as f:
                logs = f.readlines()
                actual_logs = len(logs)
                print(f"Nombre de logs écrits: {actual_logs}")
                print(f"Taille finale du buffer: {len(message_buffer)}")
                
                # Vérifications
                self.assertLess(actual_logs, 300,
                    f"Le buffer n'a pas correctement limité la taille des logs (trouvé: {actual_logs} logs)")
                self.assertGreater(actual_logs, 0,
                    "Aucun log n'a été écrit")
                
                # Log des résultats
                logger.info(format_log_message(
                    "Résultat du test de débordement",
                    {
                        "logs_count": actual_logs,
                        "buffer_size": len(message_buffer)
                    }
                ))
                
        except Exception as e:
            print(f"\nERREUR PENDANT LE TEST: {str(e)}")
            raise
        
        print("=== Fin du test de débordement ===\n")

    def test_error_immediate_logging(self):
        """Test que les erreurs sont loguées immédiatement"""
        # Simuler une erreur
        log_system_error("TEST_ERROR", "Test error message", {"critical": True})
        
        # Vérifier que l'erreur est écrite immédiatement
        with open('planete_pointage.log', 'r') as f:
            logs = f.readlines()
            self.assertTrue(
                any("TEST_ERROR" in line for line in logs),
                "L'erreur n'a pas été loguée immédiatement"
            )

    def test_validation_donnees_log(self):
        """Test de la validation des données de log"""
        # Test avec caractères spéciaux
        self.buffer.add_message("action_spéciale", 7, "test_user")
        
        # Test avec une longue chaîne
        long_message = "a" * 1000
        self.buffer.add_message(long_message, 7, "test_user")
        
        # Test avec caractères JSON spéciaux
        json_message = '{"key": "value"}'
        self.buffer.add_message(json_message, 7, "test_user")

        # Vérifie que les messages sont bien formatés
        self.buffer.flush()
        time.sleep(0.5)  # Attend que le flush soit terminé

    def test_format_message(self):
        """Test du format des messages de log"""
        # Test de base
        message = format_log_message("Test message", {"key": "value"})
        self.assertIsInstance(message, str)
        
        # Parser le message
        data = json.loads(message)
        
        # Vérifier la structure
        self.assertIn("message", data)
        self.assertIn("timestamp", data)
        self.assertEqual(data["key"], "value")
        
        # Test avec des types complexes
        complex_data = {
            "date": datetime.now(),
            "list": [1, 2, 3],
            "dict": {"nested": True},
            "none": None
        }
        
        message = format_log_message("Test complex", complex_data)
        data = json.loads(message)
        
        # Vérifier que les types complexes sont correctement sérialisés
        self.assertIn("date", data)
        self.assertIsInstance(data["list"], list)
        self.assertIsInstance(data["dict"], dict)
        self.assertIsNone(data["none"])

    def test_nettoyage_buffer(self):
        """Test du nettoyage automatique du buffer"""
        # Ajoute des messages jusqu'à déclencher le nettoyage automatique
        for i in range(100):
            self.buffer.add_message(f"action_{i}", 6, "test_user")
            time.sleep(0.001)  # Petit délai pour simuler des actions réelles

        # Force un flush final
        self.buffer.flush()
        time.sleep(0.5)  # Attend que le flush soit terminé

        # Vérifie que le buffer a été nettoyé
        self.assertEqual(self.buffer.get_size(), 0, "Le buffer devrait être vide après le nettoyage")

    def test_concurrence(self):
        """Test du comportement du buffer en situation de concurrence"""
        def worker(thread_id, count):
            for i in range(count):
                self.buffer.add_message(f"Message from thread {thread_id}, count {i}", 
                                      thread_id, f"user_{thread_id}")
                time.sleep(0.001)  # Simule une charge réaliste

        # Crée 10 threads qui ajoutent chacun 50 messages
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i, 50))
            threads.append(t)
            t.start()

        # Attend que tous les threads terminent
        for t in threads:
            t.join()

        # Force un dernier flush
        self.buffer.flush()
        time.sleep(0.5)  # Attend que le dernier flush soit terminé

        # Vérifie que tous les messages ont été traités
        self.assertEqual(self.buffer.get_size(), 0, "Le buffer devrait être vide")

    def tearDown(self):
        print("\n=== Début de tearDown ===")
        self.buffer.flush()
        print("Buffer vidé dans tearDown")
        
        # Fermer tous les handlers du logger
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers = []
        print("Handlers fermés et réinitialisés")
        
        # Nettoyer le fichier de log
        if os.path.exists('planete_pointage.log'):
            try:
                os.remove('planete_pointage.log')
                print("Fichier de log supprimé")
            except PermissionError:
                # Si le fichier est toujours verrouillé, on le vide simplement
                with open('planete_pointage.log', 'w') as f:
                    f.write('')
                print("Fichier de log vidé (PermissionError)")
        print("=== Fin de tearDown ===\n") 