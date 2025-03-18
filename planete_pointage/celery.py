import os
from celery import Celery
from celery.schedules import crontab

# Définir les variables d'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planete_pointage.settings')

# Créer l'application Celery
app = Celery('planete_pointage')

# Charger la configuration depuis Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger les tâches des applications Django
app.autodiscover_tasks()

# Planifier les tâches
app.conf.beat_schedule = {
    'verifications-quotidiennes': {
        'task': 'core.tasks.executer_verifications_quotidiennes',
        'schedule': crontab(hour=22, minute=0),  # Tous les jours à 22h00
    },
    'resume-hebdomadaire': {
        'task': 'core.tasks.generer_resume_hebdomadaire',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Tous les lundis à 8h00
    },
} 