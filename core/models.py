import re
import logging
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.utils import timezone
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler pour la console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Modèle utilisateur personnalisé
class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('manager', 'Manager'),
        ('gardien', 'Gardien'),
        ('agent_de_nettoyage', 'Agent de nettoyage'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='gardien')
    organisation = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='organisation_users')
    groups = models.ManyToManyField(Group, related_name='auth_users')

    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"{self.username} ({self.role}) - {org_name}"

# Modèle pour les sites
class Site(models.Model):
    """
    Model representing a site where time tracking occurs.
    """
    name = models.CharField(max_length=100)
    qr_code_value = models.CharField(max_length=100, unique=True)
    emails_alertes = models.TextField(blank=True)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE)
    adresse = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_email_list(self):
        """Returns list of alert emails."""
        return [email.strip() for email in self.emails_alertes.split(',') if email.strip()]
    
    def __str__(self):
        return self.name

# Service de gestion des dates
class DateService:
    @staticmethod
    def to_paris_timezone(date):
        logger.debug(f"[TRACKING DATE] to_paris_timezone - Date entrée: {date} (timezone: {date.tzinfo})")
        if timezone.is_naive(date):
            logger.debug("[TRACKING DATE] Date naïve détectée, ajout de la timezone")
            date = timezone.make_aware(date)
        result = timezone.localtime(date, timezone=ZoneInfo("Europe/Paris"))
        logger.debug(f"[TRACKING DATE] Date convertie Paris: {result} (timezone: {result.tzinfo}, offset: {result.utcoffset()})")
        return result

# Modèle pour les plannings
class Planning(models.Model):
    """
    Model representing a work schedule.
    """
    TYPE_CHOICES = [
        ('gardiennage', 'Gardiennage'),
        ('nettoyage', 'Nettoyage'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    actif = models.BooleanField(default=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    # Jours de passage
    lundi = models.BooleanField(default=False)
    mardi = models.BooleanField(default=False)
    mercredi = models.BooleanField(default=False)
    jeudi = models.BooleanField(default=False)
    vendredi = models.BooleanField(default=False)
    samedi = models.BooleanField(default=False)
    dimanche = models.BooleanField(default=False)
    
    # Horaires
    heure_debut_matin = models.TimeField(null=True, blank=True)
    heure_fin_matin = models.TimeField(null=True, blank=True)
    heure_debut_aprem = models.TimeField(null=True, blank=True)
    heure_fin_aprem = models.TimeField(null=True, blank=True)
    
    # Marges et durées
    marge_retard = models.IntegerField(default=15)  # minutes
    marge_depart_anticip = models.IntegerField(default=15)  # minutes
    duree_min = models.IntegerField(default=60)  # minutes
    frequence = models.IntegerField(default=1)  # passages par jour
    marge_duree_pct = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_jours_passage(self):
        """Returns string of working days."""
        jours = []
        if self.lundi: jours.append('L')
        if self.mardi: jours.append('M')
        if self.mercredi: jours.append('Me')
        if self.jeudi: jours.append('J')
        if self.vendredi: jours.append('V')
        if self.samedi: jours.append('S')
        if self.dimanche: jours.append('D')
        return '-'.join(jours)
    
    def __str__(self):
        return f"{self.user.username} - {self.site.name} ({self.type})"

# Modèle pour les pointages
class Pointage(models.Model):
    """
    Model representing a time tracking record.
    """
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
    ]
    
    PERIODE_CHOICES = [
        ('matin', 'Matin'),
        ('apres_midi', 'Après-midi'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    planning = models.ForeignKey(Planning, on_delete=models.SET_NULL, null=True)
    date_scan = models.DateTimeField()
    periode = models.CharField(max_length=10, choices=PERIODE_CHOICES, null=True)
    type_pointage = models.CharField(max_length=10, choices=TYPE_CHOICES)
    retard = models.IntegerField(default=0)  # minutes
    depart_anticip = models.IntegerField(default=0)  # minutes
    commentaire = models.TextField(blank=True)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def trouver_planning_associe(self):
        """Find associated planning for this pointage."""
        if not self.planning:
            self.planning = Planning.objects.filter(
                site=self.site,
                user=self.user,
                actif=True,
                date_debut__lte=self.date_scan.date(),
                date_fin__gte=self.date_scan.date()
            ).first()
    
    def creer_anomalie_si_necessaire(self):
        """Create anomaly if needed."""
        if self.retard > 0 or self.depart_anticip > 0:
            from .models import Anomalie
            Anomalie.objects.create(
                user=self.user,
                site=self.site,
                type_anomalie='retard' if self.retard > 0 else 'depart_anticipe',
                motif=f"{'Retard' if self.retard > 0 else 'Départ anticipé'} de {self.retard or self.depart_anticip} minutes",
                minutes_manquantes=self.retard or self.depart_anticip,
                organisation=self.organisation
            )
    
    def __str__(self):
        return f"{self.user.username} - {self.site.name} - {self.date_scan}"

# Modèle pour les anomalies
class Anomalie(models.Model):
    """
    Model representing a time tracking anomaly.
    """
    TYPE_CHOICES = [
        ('retard', 'Retard'),
        ('depart_anticipe', 'Départ anticipé'),
        ('absence', 'Absence'),
        ('autre', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('justifiee', 'Justifiée'),
        ('non_justifiee', 'Non justifiée'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    type_anomalie = models.CharField(max_length=20, choices=TYPE_CHOICES)
    motif = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    justificatif = models.FileField(upload_to='justificatifs/', null=True, blank=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    commentaire_traitement = models.TextField(blank=True)
    traite_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='anomalies_traitees')
    minutes_manquantes = models.IntegerField(default=0)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.site.name} - {self.type_anomalie}"

class StatistiquesTemps(models.Model):
    """
    Model for storing time statistics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    mois = models.IntegerField()
    annee = models.IntegerField()
    minutes_travaillees = models.IntegerField(default=0)
    minutes_retard = models.IntegerField(default=0)
    minutes_depart_anticipe = models.IntegerField(default=0)
    minutes_absence = models.IntegerField(default=0)
    jours_travailles = models.IntegerField(default=0)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE)
    date_derniere_maj = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def heures_travaillees(self):
        return round(self.minutes_travaillees / 60, 2)
    
    @property
    def heures_retard(self):
        return round(self.minutes_retard / 60, 2)
    
    @property
    def heures_depart_anticipe(self):
        return round(self.minutes_depart_anticipe / 60, 2)
    
    @property
    def heures_absence(self):
        return round(self.minutes_absence / 60, 2)
    
    @property
    def minutes_manquantes_total(self):
        return self.minutes_retard + self.minutes_depart_anticipe + self.minutes_absence
    
    @classmethod
    def update_from_pointages(cls, user_id, site_id):
        """Update statistics from pointages."""
        # Implementation here
        pass
    
    @classmethod
    def update_from_anomalies(cls, user_id, site_id):
        """Update statistics from anomalies."""
        # Implementation here
        pass
    
    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"Stats {self.user.username} - {self.site.name} - {org_name} - {self.mois}/{self.annee}"

__all__ = [
    'User',
    'Site',
    'Planning',
    'Pointage',
    'Anomalie',
    'DateService',
    'StatistiquesTemps',
]
