import logging
import json
from datetime import datetime
from functools import wraps
from django.conf import settings
from collections import deque
import threading
import time

# Configuration du logger principal
logger = logging.getLogger('planete_pointage')

# Buffer circulaire pour les messages en attente
message_buffer = deque(maxlen=250)  # Optimisé pour 200 pointages simultanés
buffer_lock = threading.Lock()

BATCH_SIZE = 50  # Nombre de messages à traiter par lot

def setup_logging():
    """Configure le système de logging avec des handlers optimisés pour les performances"""
    print("\n=== Configuration du logging ===")
    if logger.handlers:  # Évite la configuration multiple
        print("Logger déjà configuré, skip")
        return
        
    logger.setLevel(logging.DEBUG)  # Changé à DEBUG pour plus d'informations
    print(f"Logger level configuré à: {logger.getEffectiveLevel()}")
    
    # Formatter optimisé
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Handler pour le fichier
    file_handler = logging.FileHandler('planete_pointage.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    logger.addHandler(file_handler)
    print(f"Handler ajouté au logger. Total handlers: {len(logger.handlers)}")
    print("=== Fin de la configuration du logging ===\n")

def format_log_message(message, extra=None):
    """Formate un message de log avec des informations supplémentaires"""
    log_data = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
    }
    if extra:
        log_data.update(extra)
    return json.dumps(log_data, default=str)

def flush_buffer():
    """Force l'écriture du buffer de messages"""
    print("\n=== Début du flush du buffer ===")
    print(f"Taille du buffer avant flush: {len(message_buffer)}")
    
    try:
        with buffer_lock:
            if message_buffer:
                messages_to_flush = list(message_buffer)  # Copie du buffer
                message_buffer.clear()  # Vider le buffer immédiatement
                print(f"Buffer copié et vidé. Messages à traiter: {len(messages_to_flush)}")
            else:
                print("Buffer déjà vide")
                return
    
        # Traiter les messages en dehors du lock
        for msg in messages_to_flush:
            try:
                formatted_msg = format_log_message("Action buffered", msg)
                print(f"Écriture du message: {formatted_msg[:100]}...")
                logger.info(formatted_msg)
            except Exception as e:
                print(f"Erreur lors de l'écriture d'un message: {str(e)}")
        print("Messages traités")
        
    except Exception as e:
        print(f"Erreur lors du flush du buffer: {str(e)}")
    
    print(f"Taille du buffer après flush: {len(message_buffer)}")
    print("=== Fin du flush du buffer ===\n")

def log_user_action(user, action, details=None):
    """Log une action utilisateur"""
    print(f"\n=== Log d'action utilisateur: {action} ===")
    log_data = {
        'user_id': user.id if user else None,
        'username': user.username if user else None,
        'action': action
    }
    if details:
        log_data['details'] = details
    
    with buffer_lock:
        message_buffer.append(log_data)
        print(f"Action ajoutée au buffer. Taille actuelle: {len(message_buffer)}")
        if len(message_buffer) >= BATCH_SIZE:
            print("Taille du batch atteinte, flush automatique")
            
    if len(message_buffer) >= BATCH_SIZE:
        flush_buffer()
            
    print("=== Fin du log d'action utilisateur ===\n")

def log_system_error(error_type, error_message, details=None):
    """Log une erreur système - traitement immédiat sans buffer"""
    print(f"\n=== Log d'erreur système: {error_type} ===")
    log_data = {
        'error_type': error_type,
        'error_message': error_message
    }
    if details:
        log_data['details'] = details
    
    formatted_msg = format_log_message("Erreur système", log_data)
    logger.error(formatted_msg)
    print("Erreur loguée")
    flush_buffer()
    print("=== Fin du log d'erreur système ===\n")

# Initialisation du logging au démarrage
setup_logging() 