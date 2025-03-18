from django.db import models
from django.core.exceptions import ValidationError
from .base import OrganisationModel
import re
from django.utils import timezone
import logging
from .statistiques import StatistiquesTemps

logger = logging.getLogger(__name__)

class Anomalie(OrganisationModel):
    """
    Modèle pour les anomalies de pointage (retards, absences, etc.)
    """
    TYPE_ANOMALIE_CHOICES = [
        ('retard', 'Retard'),
        ('depart_anticipe', 'Départ anticipé'),
        ('absence', 'Absence'),
        ('autre', 'Autre')
    ]
    
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('justifiee', 'Justifiée'),
        ('non_justifiee', 'Non justifiée'),
        ('en_cours', 'En cours de traitement')
    ]
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='anomalies',
        verbose_name="Utilisateur"
    )
    site = models.ForeignKey(
        'Site',
        on_delete=models.CASCADE,
        related_name='anomalies',
        verbose_name="Site"
    )
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    type_anomalie = models.CharField(
        max_length=20,
        choices=TYPE_ANOMALIE_CHOICES,
        default='autre',
        verbose_name="Type d'anomalie"
    )
    motif = models.TextField(
        verbose_name="Motif"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='en_attente',
        verbose_name="Statut"
    )
    justificatif = models.FileField(
        upload_to='justificatifs/',
        null=True,
        blank=True,
        verbose_name="Justificatif"
    )
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de traitement"
    )
    commentaire_traitement = models.TextField(
        null=True,
        blank=True,
        verbose_name="Commentaire de traitement"
    )
    traite_par = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anomalies_traitees',
        verbose_name="Traité par"
    )
    minutes_manquantes = models.IntegerField(
        default=0,
        verbose_name="Minutes manquantes",
        help_text="Nombre de minutes manquantes (retard, départ anticipé, absence)"
    )
    
    class Meta:
        verbose_name = "Anomalie"
        verbose_name_plural = "Anomalies"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['user', 'date_creation']),
            models.Index(fields=['site', 'date_creation']),
            models.Index(fields=['type_anomalie']),
            models.Index(fields=['status']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.get_type_anomalie_display()} - {self.date_creation.strftime('%d/%m/%Y')}"
        
    def save(self, *args, **kwargs):
        """
        Sauvegarde l'anomalie et met à jour les statistiques
        """
        # Si l'organisation n'est pas définie, utiliser celle du site
        if not self.organisation and self.site and self.site.organisation:
            self.organisation = self.site.organisation
            
        # Calculer les minutes manquantes si nécessaire
        self.extraire_minutes_du_motif()
        
        # Définir la date de traitement si le statut change
        old_instance = None
        if self.pk:
            try:
                old_instance = Anomalie.objects.get(pk=self.pk)
            except Anomalie.DoesNotExist:
                pass
                
        if old_instance and old_instance.status != self.status and self.status in ['justifiee', 'non_justifiee']:
            self.date_traitement = timezone.now()
            
        # Sauvegarder l'instance
        super().save(*args, **kwargs)
        
        # Mettre à jour les statistiques
        try:
            StatistiquesTemps.update_from_anomalies(
                user_id=self.user.id,
                site_id=self.site.id,
                date=self.date_creation
            )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {str(e)}")
            
    def extraire_minutes_du_motif(self):
        """
        Extrait le nombre de minutes manquantes du motif si possible
        """
        if self.minutes_manquantes > 0:
            return
            
        try:
            # Chercher un pattern comme "Retard de X minutes"
            import re
            pattern = r"(?:de|d'|)\s*(\d+)\s*minutes"
            match = re.search(pattern, self.motif)
            
            if match:
                self.minutes_manquantes = int(match.group(1))
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des minutes du motif: {str(e)}")
            
    def get_date_creation_formatted(self):
        """
        Retourne la date de création formatée
        """
        return self.date_creation.strftime("%d/%m/%Y %H:%M")
        
    def get_date_traitement_formatted(self):
        """
        Retourne la date de traitement formatée
        """
        if self.date_traitement:
            return self.date_traitement.strftime("%d/%m/%Y %H:%M")
        return "Non traité"

    def marquer_comme_traitee(self, commentaire=None):
        """Marque l'anomalie comme traitée"""
        from django.utils import timezone
        self.status = 'validee'
        self.date_traitement = timezone.now()
        if commentaire:
            self.commentaire_traitement = commentaire
        self.save() 