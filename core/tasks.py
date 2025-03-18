from celery import shared_task
from django.utils import timezone
from .services import PointageService, EmailService, MetriquesService
import logging

logger = logging.getLogger(__name__)

@shared_task
def executer_verifications_quotidiennes():
    """Tâche planifiée pour exécuter les vérifications à 22h"""
    logger.info("[TACHES] Démarrage des vérifications quotidiennes")
    debut = timezone.now()
    
    try:
        # Exécuter les vérifications
        PointageService.executer_batch_verifications()
        
        # Analyser les performances
        MetriquesService.analyser_performances_quotidiennes()
        
        # Mesurer le temps total d'exécution
        fin = timezone.now()
        MetriquesService.mesurer_temps_traitement(debut, fin, "verifications_quotidiennes")
        
        logger.info("[TACHES] Fin des vérifications quotidiennes")
        return True
        
    except Exception as e:
        logger.error(f"[TACHES] Erreur lors des vérifications quotidiennes: {str(e)}")
        return False

@shared_task
def generer_resume_hebdomadaire():
    """Tâche planifiée pour générer et envoyer le résumé hebdomadaire (lundi matin)"""
    logger.info("[TACHES] Génération du résumé hebdomadaire")
    debut = timezone.now()
    
    try:
        # Envoyer le résumé hebdomadaire
        EmailService.envoyer_resume_hebdomadaire()
        
        # Mesurer le temps d'exécution
        fin = timezone.now()
        MetriquesService.mesurer_temps_traitement(debut, fin, "resume_hebdomadaire")
        
        logger.info("[TACHES] Fin de la génération du résumé hebdomadaire")
        return True
        
    except Exception as e:
        logger.error(f"[TACHES] Erreur lors de la génération du résumé hebdomadaire: {str(e)}")
        return False 