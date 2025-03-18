from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .base import OrganisationModel, logger
from .services import DateService
from datetime import time

class Planning(OrganisationModel):
    """
    Modèle représentant un planning de travail
    """
    TYPE_CHOICES = [
        ('FIXE', 'Fixe'),
        ('FREQUENCE', 'Fréquence')
    ]
    
    # Relations
    site = models.ForeignKey(
        'Site',
        on_delete=models.CASCADE,
        verbose_name="Site"
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='plannings',
        verbose_name="Utilisateur",
        null=True,
        blank=True
    )
    
    # Champs de base
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Type de planning"
    )
    actif = models.BooleanField(
        default=True,
        help_text="Indique si le planning est actif"
    )
    date_debut = models.DateField(
        null=True,
        blank=True,
        help_text="Date de début d'application du planning"
    )
    date_fin = models.DateField(
        null=True,
        blank=True,
        help_text="Date de fin d'application du planning"
    )
    
    # Jours de passage
    lundi = models.BooleanField(default=False, verbose_name="Lundi")
    mardi = models.BooleanField(default=False, verbose_name="Mardi")
    mercredi = models.BooleanField(default=False, verbose_name="Mercredi")
    jeudi = models.BooleanField(default=False, verbose_name="Jeudi")
    vendredi = models.BooleanField(default=False, verbose_name="Vendredi")
    samedi = models.BooleanField(default=False, verbose_name="Samedi")
    dimanche = models.BooleanField(default=False, verbose_name="Dimanche")
    
    # Champs pour planning FIXE
    heure_debut_matin = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée le matin")
    heure_fin_matin = models.TimeField(null=True, blank=True, verbose_name="Heure de départ le midi")
    heure_debut_aprem = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée l'après-midi")
    heure_fin_aprem = models.TimeField(null=True, blank=True, verbose_name="Heure de départ le soir")
    marge_retard = models.IntegerField(default=15, verbose_name="Tolérance de retard (en minutes)")
    marge_depart_anticip = models.IntegerField(default=15, verbose_name="Tolérance de départ anticipé (en minutes)")
    
    # Champs pour planning FREQUENCE
    duree_min = models.IntegerField(null=True, blank=True, verbose_name="Durée prévue (en minutes)")
    frequence = models.IntegerField(null=True, blank=True, verbose_name="Fréquence (en jours)")
    marge_duree_pct = models.IntegerField(default=10, verbose_name="Marge de tolérance sur la durée (%)")

    class Meta:
        verbose_name = "Planning"
        verbose_name_plural = "Plannings"
        ordering = ['-actif', 'site__name']

    def __str__(self):
        jours = self.get_jours_passage()
        return f"{self.site.name} - {self.type} - {jours}"

    def get_jours_passage(self):
        """Retourne une chaîne représentant les jours de passage"""
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
        """Validation du modèle"""
        # Vérification de l'organisation
        if self.site and self.organisation and self.site.organisation != self.organisation:
            raise ValidationError("Le site doit appartenir à la même organisation que le planning.")
            
        if self.user and self.user.organisation and self.organisation and self.user.organisation != self.organisation:
            raise ValidationError("L'utilisateur doit appartenir à la même organisation que le planning.")
        
        # Vérification des jours
        if not any([self.lundi, self.mardi, self.mercredi, self.jeudi, self.vendredi, self.samedi, self.dimanche]):
            raise ValidationError("Vous devez sélectionner au moins un jour de passage.")
        
        # Validation spécifique au type
        if self.type == 'FIXE':
            self._validate_fixed_planning()
        elif self.type == 'FREQUENCE':
            self._validate_frequency_planning()
            
        # Vérification des dates
        if self.date_debut and self.date_fin and self.date_debut > self.date_fin:
            raise ValidationError("La date de début doit être antérieure à la date de fin.")
        
        # Mise à jour de l'état actif
        if self.date_fin and self.date_fin < timezone.now().date():
            self.actif = False

    def _validate_fixed_planning(self):
        """Validation spécifique pour un planning fixe"""
        matin_rempli = bool(self.heure_debut_matin) and bool(self.heure_fin_matin)
        aprem_rempli = bool(self.heure_debut_aprem) and bool(self.heure_fin_aprem)
        
        if not (matin_rempli or aprem_rempli):
            raise ValidationError("Pour un planning FIXE, vous devez renseigner au moins une période (matin ou après-midi).")
        
        if (bool(self.heure_debut_matin) != bool(self.heure_fin_matin)) or \
           (bool(self.heure_debut_aprem) != bool(self.heure_fin_aprem)):
            raise ValidationError("Les heures de début et de fin doivent être renseignées par paire.")
        
        # Réinitialisation des champs FREQUENCE
        self.duree_min = None
        self.frequence = None
        self.marge_duree_pct = 10

    def _validate_frequency_planning(self):
        """Validation spécifique pour un planning à fréquence"""
        if not self.duree_min:
            raise ValidationError("Pour un planning FREQUENCE, la durée prévue doit être renseignée.")
        
        # Réinitialisation des champs FIXE
        self.heure_debut_matin = None
        self.heure_fin_matin = None
        self.heure_debut_aprem = None
        self.heure_fin_aprem = None
        self.marge_retard = 15
        self.marge_depart_anticip = 15

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
        """Détermine la période (MATIN/APRES_MIDI) pour un scan donné"""
        logger.debug(f"[TRACKING DATE] determiner_periode - Date entrée: {date_scan} (timezone: {date_scan.tzinfo})")
        date_scan = DateService.to_paris_timezone(date_scan)
        logger.debug(f"[TRACKING DATE] Date après conversion Paris: {date_scan}")
        heure = date_scan.time()
        logger.debug(f"[TRACKING DATE] Heure extraite: {heure}")
        
        if self.type == 'FIXE':
            return self._determiner_periode_fixe(heure)
        else:
            return self._determiner_periode_frequence(heure)

    def _determiner_periode_fixe(self, heure):
        """Détermine la période pour un planning fixe"""
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

    def _determiner_periode_frequence(self, heure):
        """Détermine la période pour un planning à fréquence"""
        logger.debug("[TRACKING DATE] Planning FREQUENCE - Vérification par rapport à midi")
        midi = time(12, 0)
        logger.debug(f"[TRACKING DATE] Comparaison avec midi: {midi}")
        if heure < midi:
            logger.debug("[TRACKING DATE] Période MATIN détectée (avant 12h)")
            return 'MATIN'
        else:
            logger.debug("[TRACKING DATE] Période APRES_MIDI détectée (après 12h)")
            return 'APRES_MIDI' 