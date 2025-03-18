import re
import logging
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.utils import timezone
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.conf import settings

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
    ROLE_CHOICES = (
        ('gardien', 'Gardien'),
        ('agent_de_nettoyage', 'Agent de nettoyage'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='gardien')
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='users', verbose_name="Organisation", null=True, blank=True)

    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"{self.username} ({self.role}) - {org_name}"

# Modèle pour les sites
class Site(models.Model):
    name = models.CharField(max_length=100)
    qr_code_value = models.CharField(max_length=100)
    emails_alertes = models.TextField(blank=True, null=True)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='sites', verbose_name="Organisation", null=True, blank=True)

    class Meta:
        unique_together = [('name', 'organisation'), ('qr_code_value', 'organisation')]

    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"{self.name} - {org_name}"

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
    TYPE_CHOICES = [
        ('FIXE', 'Fixe'),
        ('FREQUENCE', 'Fréquence')
    ]
    
    site = models.ForeignKey('Site', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plannings', verbose_name="Utilisateur", null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    actif = models.BooleanField(default=True, help_text="Indique si le planning est actif")
    date_debut = models.DateField(null=True, blank=True, help_text="Date de début d'application du planning")
    date_fin = models.DateField(null=True, blank=True, help_text="Date de fin d'application du planning")
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='plannings', verbose_name="Organisation", null=True, blank=True)
    
    # Jours de passage
    lundi = models.BooleanField(default=False, verbose_name="Lundi")
    mardi = models.BooleanField(default=False, verbose_name="Mardi")
    mercredi = models.BooleanField(default=False, verbose_name="Mercredi")
    jeudi = models.BooleanField(default=False, verbose_name="Jeudi")
    vendredi = models.BooleanField(default=False, verbose_name="Vendredi")
    samedi = models.BooleanField(default=False, verbose_name="Samedi")
    dimanche = models.BooleanField(default=False, verbose_name="Dimanche")
    
    # Heures pour planning FIXE uniquement
    heure_debut_matin = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée le matin")
    heure_fin_matin = models.TimeField(null=True, blank=True, verbose_name="Heure de départ le midi")
    heure_debut_aprem = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée l'après-midi")
    heure_fin_aprem = models.TimeField(null=True, blank=True, verbose_name="Heure de départ le soir")
    marge_retard = models.IntegerField(default=15, verbose_name="Tolérance de retard (en minutes)")
    marge_depart_anticip = models.IntegerField(default=15, verbose_name="Tolérance de départ anticipé (en minutes)")
    
    # Pour planning FREQUENCE uniquement
    duree_min = models.IntegerField(null=True, blank=True, verbose_name="Durée prévue (en minutes)")
    frequence = models.IntegerField(null=True, blank=True, verbose_name="Fréquence (en jours)")
    marge_duree_pct = models.IntegerField(default=10, verbose_name="Marge de tolérance sur la durée (%)")

    class Meta:
        verbose_name = "Planning"
        verbose_name_plural = "Plannings"

    def __str__(self):
        jours = self.get_jours_passage()
        return f"{self.site.name} - {self.type} - {jours}"

    def get_jours_passage(self):
        jours = []
        if self.lundi: jours.append('lundi')
        if self.mardi: jours.append('mardi')
        if self.mercredi: jours.append('mercredi')
        if self.jeudi: jours.append('jeudi')
        if self.vendredi: jours.append('vendredi')
        if self.samedi: jours.append('samedi')
        if self.dimanche: jours.append('dimanche')
        return ','.join(jours)

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Vérifier que le site et l'utilisateur appartiennent à la même organisation
        if self.site and self.organisation and self.site.organisation != self.organisation:
            raise ValidationError("Le site doit appartenir à la même organisation que le planning.")
            
        if self.user and self.user.organisation and self.organisation and self.user.organisation != self.organisation:
            raise ValidationError("L'utilisateur doit appartenir à la même organisation que le planning.")
        
        # Vérifier qu'au moins un jour est sélectionné
        if not any([self.lundi, self.mardi, self.mercredi, self.jeudi, self.vendredi, self.samedi, self.dimanche]):
            raise ValidationError("Vous devez sélectionner au moins un jour de passage.")
        
        if self.type == 'FIXE':
            # Vérifier que les champs FIXE sont remplis par paire (matin ou après-midi)
            matin_rempli = bool(self.heure_debut_matin) and bool(self.heure_fin_matin)
            aprem_rempli = bool(self.heure_debut_aprem) and bool(self.heure_fin_aprem)
            
            if not (matin_rempli or aprem_rempli):
                raise ValidationError("Pour un planning FIXE, vous devez renseigner au moins une période (matin ou après-midi).")
            
            if (bool(self.heure_debut_matin) != bool(self.heure_fin_matin)) or \
               (bool(self.heure_debut_aprem) != bool(self.heure_fin_aprem)):
                raise ValidationError("Les heures de début et de fin doivent être renseignées par paire.")
            
            # Réinitialiser les champs FREQUENCE
            self.duree_min = None
            self.frequence = None
            self.marge_duree_pct = 10
            
        elif self.type == 'FREQUENCE':
            # Vérifier que les champs FREQUENCE sont remplis
            if not self.duree_min:
                raise ValidationError("Pour un planning FREQUENCE, la durée prévue doit être renseignée.")
            
            # Réinitialiser les champs FIXE
            self.heure_debut_matin = None
            self.heure_fin_matin = None
            self.heure_debut_aprem = None
            self.heure_fin_aprem = None
            self.marge_retard = 15
            self.marge_depart_anticip = 15
            
        # Vérifier la cohérence des dates
        if self.date_debut and self.date_fin and self.date_debut > self.date_fin:
            raise ValidationError("La date de début doit être antérieure à la date de fin.")
        
        # Vérifier l'état actif en fonction de la date_fin
        if self.date_fin:
            if self.date_fin < timezone.now().date():
                self.actif = False
            else:
                self.actif = True

    def est_actif(self, date=None):
        """Vérifie si le planning est actif à une date donnée"""
        if not self.actif:
            return False
            
        if not date:
            date = timezone.localtime().date()
            
        if self.date_debut and date < self.date_debut:
            return False
            
        if self.date_fin and date > self.date_fin:
            return False
            
        return True

    def determiner_periode(self, date_scan):
        logger.debug(f"[TRACKING DATE] determiner_periode - Date entrée: {date_scan} (timezone: {date_scan.tzinfo})")
        date_scan = DateService.to_paris_timezone(date_scan)
        logger.debug(f"[TRACKING DATE] Date après conversion Paris: {date_scan}")
        heure = date_scan.time()
        logger.debug(f"[TRACKING DATE] Heure extraite: {heure}")
        
        if self.type == 'FIXE':
            logger.debug("[TRACKING DATE] Planning FIXE - Vérification des plages horaires")
            if self.heure_debut_matin and self.heure_fin_matin:
                logger.debug(f"[TRACKING DATE] Vérification période MATIN - entre {self.heure_debut_matin} et {self.heure_fin_matin}")
                if self.heure_debut_matin <= heure <= self.heure_fin_matin:
                    logger.debug("[TRACKING DATE] Période MATIN détectée")
                    return 'MATIN'
                    
            if self.heure_debut_aprem and self.heure_fin_aprem:
                logger.debug(f"[TRACKING DATE] Vérification période APRES_MIDI - entre {self.heure_debut_aprem} et {self.heure_fin_aprem}")
                if self.heure_debut_aprem <= heure <= self.heure_fin_aprem:
                    logger.debug("[TRACKING DATE] Période APRES_MIDI détectée")
                    return 'APRES_MIDI'
                    
            logger.debug("[TRACKING DATE] Aucune période détectée pour planning FIXE")
            return None
        else:  # FREQUENCE
            logger.debug("[TRACKING DATE] Planning FREQUENCE - Vérification par rapport à midi")
            midi = time(12, 0)
            logger.debug(f"[TRACKING DATE] Comparaison avec midi: {midi}")
            if heure < midi:
                logger.debug("[TRACKING DATE] Période MATIN détectée (avant 12h)")
                return 'MATIN'
            else:
                logger.debug("[TRACKING DATE] Période APRES_MIDI détectée (après 12h)")
                return 'APRES_MIDI'

    def calculer_retard(self, date_scan, periode, user):
        """Calcule le retard en minutes et crée une anomalie si nécessaire"""
        if self.type != 'FIXE':
            return 0
            
        heure_debut = self.heure_debut_matin if periode == 'MATIN' else self.heure_debut_aprem
        if not heure_debut:
            return 0
            
        # Convertir l'heure de début en datetime
        date_debut = datetime.combine(date_scan.date(), heure_debut)
        date_debut = DateService.to_paris_timezone(date_debut)
        
        # Calculer le retard en minutes
        retard = (date_scan - date_debut).total_seconds() / 60
        
        # Si le retard dépasse la marge
        if retard > self.marge_retard:
            # Créer une anomalie
            Anomalie.objects.create(
                user=user,
                site=self.site,
                motif=f"Retard de {int(retard)} minutes",
                type_anomalie='retard',
                organisation=self.organisation
            )
            return int(retard)
            
        return 0

    def calculer_depart_anticipe(self, date_scan, periode, user):
        """Calcule le départ anticipé en minutes et crée une anomalie si nécessaire"""
        if self.type != 'FIXE':
            return 0
            
        heure_fin = self.heure_fin_matin if periode == 'MATIN' else self.heure_fin_aprem
        if not heure_fin:
            return 0
            
        # Convertir l'heure de fin en datetime
        date_fin = datetime.combine(date_scan.date(), heure_fin)
        date_fin = DateService.to_paris_timezone(date_fin)
        
        # Calculer le départ anticipé en minutes
        depart_anticipe = (date_fin - date_scan).total_seconds() / 60
        
        # Si le départ est anticipé et dépasse la marge
        if depart_anticipe > self.marge_depart_anticip:
            # Créer une anomalie
            Anomalie.objects.create(
                user=user,
                site=self.site,
                motif=f"Départ anticipé de {int(depart_anticipe)} minutes",
                type_anomalie='depart_anticipe',
                organisation=self.organisation
            )
            return int(depart_anticipe)
            
        return 0

# Modèle pour les pointages
class Pointage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE, null=True)
    date_scan = models.DateTimeField()
    retard = models.IntegerField(default=0)
    depart_anticip = models.IntegerField(default=0)
    ecart_duree_minutes = models.IntegerField(default=0, help_text="Écart par rapport à la durée prévue (pour planning FREQUENCE)")
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='pointages', verbose_name="Organisation", null=True, blank=True)

    class Meta:
        ordering = ['date_scan']  # Pour assurer l'ordre chronologique

    def save(self, *args, **kwargs):
        # Vérifier la cohérence de l'organisation
        if self.organisation:
            if (self.user.organisation and self.user.organisation != self.organisation) or \
               (self.site.organisation and self.site.organisation != self.organisation) or \
               (self.planning and self.planning.organisation and self.planning.organisation != self.organisation):
                raise ValidationError("L'utilisateur, le site et le planning doivent appartenir à la même organisation que le pointage.")

        # Calculer l'écart de durée pour les plannings FREQUENCE
        if self.planning and self.planning.type == 'FREQUENCE':
            pointages_jour = Pointage.objects.filter(
                user=self.user,
                site=self.site,
                date_scan__date=self.date_scan.date()
            ).order_by('date_scan')
            
            if len(pointages_jour) >= 2:  # Si au moins une entrée et une sortie
                duree = (pointages_jour.last().date_scan - pointages_jour.first().date_scan).total_seconds() / 60
                marge_min = self.planning.duree_min * (1 - self.planning.marge_duree_pct/100)
                if duree < marge_min:
                    self.ecart_duree_minutes = int(self.planning.duree_min - duree)
                    Anomalie.objects.create(
                        user=self.user,
                        site=self.site,
                        motif=f"Durée de présence insuffisante: {int(duree)} minutes au lieu de {self.planning.duree_min} minutes",
                        type_anomalie='presence_partielle',
                        organisation=self.organisation
                    )

# Modèle pour les anomalies
class Anomalie(models.Model):
    TYPE_CHOICES = [
        ('retard', 'Retard'),
        ('depart_anticipe', 'Départ anticipé'),
        ('absence', 'Absence'),
        ('presence_partielle', 'Présence partielle'),
        ('incoherence', 'Incohérence')
    ]
    
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    motif = models.CharField(max_length=255)
    date_declaration = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    type_anomalie = models.CharField(max_length=20, choices=TYPE_CHOICES)
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='anomalies', verbose_name="Organisation", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Vérifier la cohérence de l'organisation si elle est définie
        if self.organisation:
            if (self.user.organisation and self.user.organisation != self.organisation) or \
               (self.site.organisation and self.site.organisation != self.organisation):
                raise ValidationError("L'utilisateur et le site doivent appartenir à la même organisation que l'anomalie.")
            
        # Extraire la durée du motif (ex: "Retard de 15 minutes")
        match = re.search(r'(\d+) minutes', self.motif)
        if match:
            duree = int(match.group(1))
            
            # Récupérer ou créer les statistiques pour ce mois
            date = self.date_declaration
            stats, created = StatistiquesTemps.objects.get_or_create(
                user=self.user,
                site=self.site,
                organisation=self.organisation,
                mois=date.month,
                annee=date.year
            )
            
            # Mettre à jour les statistiques selon le type d'anomalie
            if self.type_anomalie == 'retard':
                stats.minutes_retard += duree
            elif self.type_anomalie == 'depart_anticipe':
                stats.minutes_depart_anticipe += duree
            elif self.type_anomalie in ['absence', 'presence_partielle']:
                stats.minutes_absence += duree
            
            # Sauvegarder les statistiques
            stats.save()
        
        super().save(*args, **kwargs)

class StatistiquesTemps(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statistiques_temps')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='statistiques_temps')
    organisation = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='statistiques_temps', verbose_name="Organisation", null=True, blank=True)
    mois = models.IntegerField()
    annee = models.IntegerField()
    minutes_retard = models.IntegerField(default=0, help_text="Total des minutes de retard sur le mois")
    minutes_depart_anticipe = models.IntegerField(default=0, help_text="Total des minutes de départ anticipé sur le mois")
    minutes_absence = models.IntegerField(default=0, help_text="Total des minutes d'absence sur le mois")
    
    class Meta:
        unique_together = ('user', 'site', 'organisation', 'mois', 'annee')
        verbose_name = "Statistique de temps"
        verbose_name_plural = "Statistiques de temps"

    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"Stats {self.user.username} - {self.site.name} - {org_name} - {self.mois}/{self.annee}"
        
    @property
    def minutes_manquantes_total(self):
        """Calcule le total des minutes manquantes"""
        return (
            self.minutes_retard +          # Minutes de retard
            self.minutes_depart_anticipe + # Minutes de départ anticipé
            self.minutes_absence           # Minutes d'absence (incluant présence partielle)
        )
        
    @property
    def heures_manquantes(self):
        """Convertit les minutes en heures pour affichage"""
        return round(self.minutes_manquantes_total / 60, 2)

    def update_from_anomalies(self):
        """Met à jour les statistiques à partir des anomalies du mois"""
        # Réinitialiser les compteurs
        self.minutes_retard = 0
        self.minutes_depart_anticipe = 0
        self.minutes_absence = 0
        
        # Récupérer toutes les anomalies du mois
        anomalies = Anomalie.objects.filter(
            user=self.user,
            site=self.site,
            organisation=self.organisation,
            date_declaration__month=self.mois,
            date_declaration__year=self.annee
        )
        
        # Calculer les totaux par type d'anomalie
        for anomalie in anomalies:
            match = re.search(r'(\d+) minutes', anomalie.motif)
            if match:
                minutes = int(match.group(1))
                if anomalie.type_anomalie == 'retard':
                    self.minutes_retard += minutes
                elif anomalie.type_anomalie == 'depart_anticipe':
                    self.minutes_depart_anticipe += minutes
                elif anomalie.type_anomalie in ['absence', 'presence_partielle']:
                    self.minutes_absence += minutes
        
        self.save()

__all__ = [
    'User',
    'Site',
    'Planning',
    'Pointage',
    'Anomalie',
    'DateService',
]
