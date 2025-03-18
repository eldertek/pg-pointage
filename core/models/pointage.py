from django.db import models
from django.utils import timezone
from .base import OrganisationModel, logger
from .services import DateService
import logging

logger = logging.getLogger(__name__)

class Pointage(OrganisationModel):
    """
    Modèle représentant un pointage d'un utilisateur sur un site
    """
    PERIODE_CHOICES = [
        ('MATIN', 'Matin'),
        ('APRES_MIDI', 'Après-midi'),
        ('HORS_PLAGE', 'Hors plage')
    ]
    
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie')
    ]
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='pointages',
        verbose_name="Utilisateur"
    )
    site = models.ForeignKey(
        'Site',
        on_delete=models.CASCADE,
        related_name='pointages',
        verbose_name="Site"
    )
    date_scan = models.DateTimeField(
        verbose_name="Date et heure du scan"
    )
    periode = models.CharField(
        max_length=20,
        choices=PERIODE_CHOICES,
        default='HORS_PLAGE',
        verbose_name="Période"
    )
    type_pointage = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='ENTREE',
        verbose_name="Type de pointage"
    )
    planning = models.ForeignKey(
        'Planning',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pointages',
        verbose_name="Planning associé"
    )
    retard = models.IntegerField(
        default=0,
        verbose_name="Retard (minutes)",
        help_text="Nombre de minutes de retard"
    )
    depart_anticip = models.IntegerField(
        default=0,
        verbose_name="Départ anticipé (minutes)",
        help_text="Nombre de minutes de départ anticipé"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )

    class Meta:
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        ordering = ['-date_scan']
        indexes = [
            models.Index(fields=['user', 'date_scan']),
            models.Index(fields=['site', 'date_scan']),
            models.Index(fields=['date_scan']),
            models.Index(fields=['periode']),
            models.Index(fields=['type_pointage']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.site.name} - {self.date_scan.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Si l'organisation n'est pas définie, utiliser celle du site
        if not self.organisation and self.site and self.site.organisation:
            self.organisation = self.site.organisation
            
        # Attribuer la période automatiquement si elle n'est pas déjà définie
        if not self.periode or self.periode == 'HORS_PLAGE':
            current_hour = self.date_scan.hour
            if 5 <= current_hour < 12:  # Entre 5h et 12h
                self.periode = 'MATIN'
            elif 12 <= current_hour < 22:  # Entre 12h et 22h
                self.periode = 'APRES_MIDI'
                
        # Vérifier la cohérence avec le planning
        if not self.planning:
            self.trouver_planning_associe()
            
        # Calculer les retards/départs anticipés si nécessaire
        if self.planning and self.planning.type == 'FIXE':
            self.calculer_anomalies()
            
        # Conversion de la date en timezone Paris
        if self.date_scan:
            self.date_scan = DateService.to_paris_timezone(self.date_scan)
        
        super().save(*args, **kwargs)

    def trouver_planning_associe(self):
        """Trouve le planning associé à ce pointage"""
        from .planning import Planning
        
        try:
            # Déterminer le jour de la semaine (1=Lundi, 7=Dimanche)
            jour_semaine = self.date_scan.isoweekday()
            
            # Filtre pour le jour de la semaine
            filtres_jour = {}
            if jour_semaine == 1:
                filtres_jour['lundi'] = True
            elif jour_semaine == 2:
                filtres_jour['mardi'] = True
            elif jour_semaine == 3:
                filtres_jour['mercredi'] = True
            elif jour_semaine == 4:
                filtres_jour['jeudi'] = True
            elif jour_semaine == 5:
                filtres_jour['vendredi'] = True
            elif jour_semaine == 6:
                filtres_jour['samedi'] = True
            elif jour_semaine == 7:
                filtres_jour['dimanche'] = True
            
            # Rechercher un planning actif pour ce jour, ce site et cet utilisateur
            plannings = Planning.objects.filter(
                actif=True,
                site=self.site,
                user=self.user,
                **filtres_jour
            ).order_by('-date_debut')
            
            if plannings.exists():
                self.planning = plannings.first()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'un planning: {str(e)}")
            return False
            
    def calculer_anomalies(self):
        """Calcule les retards et départs anticipés"""
        if not self.planning or self.planning.type != 'FIXE':
            return False
            
        try:
            # Heure du pointage
            heure_pointage = self.date_scan.time()
            
            # Vérifier s'il s'agit d'un retard
            if self.type_pointage == 'ENTREE':
                if self.periode == 'MATIN' and self.planning.heure_debut_matin:
                    # Calculer les minutes de retard pour le matin
                    heure_attendue = self.planning.heure_debut_matin
                    
                    if heure_pointage > heure_attendue:
                        minutes_retard = (
                            heure_pointage.hour * 60 + heure_pointage.minute -
                            heure_attendue.hour * 60 - heure_attendue.minute
                        )
                        
                        # Appliquer la marge de tolérance
                        if minutes_retard > self.planning.marge_retard:
                            self.retard = minutes_retard
                            
                elif self.periode == 'APRES_MIDI' and self.planning.heure_debut_aprem:
                    # Calculer les minutes de retard pour l'après-midi
                    heure_attendue = self.planning.heure_debut_aprem
                    
                    if heure_pointage > heure_attendue:
                        minutes_retard = (
                            heure_pointage.hour * 60 + heure_pointage.minute -
                            heure_attendue.hour * 60 - heure_attendue.minute
                        )
                        
                        # Appliquer la marge de tolérance
                        if minutes_retard > self.planning.marge_retard:
                            self.retard = minutes_retard
                            
            # Vérifier s'il s'agit d'un départ anticipé
            elif self.type_pointage == 'SORTIE':
                if self.periode == 'MATIN' and self.planning.heure_fin_matin:
                    # Calculer les minutes de départ anticipé pour le matin
                    heure_attendue = self.planning.heure_fin_matin
                    
                    if heure_pointage < heure_attendue:
                        minutes_depart = (
                            heure_attendue.hour * 60 + heure_attendue.minute -
                            heure_pointage.hour * 60 - heure_pointage.minute
                        )
                        
                        # Appliquer la marge de tolérance
                        if minutes_depart > self.planning.marge_depart_anticip:
                            self.depart_anticip = minutes_depart
                            
                elif self.periode == 'APRES_MIDI' and self.planning.heure_fin_aprem:
                    # Calculer les minutes de départ anticipé pour l'après-midi
                    heure_attendue = self.planning.heure_fin_aprem
                    
                    if heure_pointage < heure_attendue:
                        minutes_depart = (
                            heure_attendue.hour * 60 + heure_attendue.minute -
                            heure_pointage.hour * 60 - heure_pointage.minute
                        )
                        
                        # Appliquer la marge de tolérance
                        if minutes_depart > self.planning.marge_depart_anticip:
                            self.depart_anticip = minutes_depart
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des anomalies: {str(e)}")
            return False
            
    def creer_anomalie_si_necessaire(self):
        """Crée une anomalie si un retard ou départ anticipé est détecté"""
        from .anomalie import Anomalie
        
        try:
            if self.retard > 0:
                # Créer une anomalie de retard
                anomalie = Anomalie(
                    user=self.user,
                    site=self.site,
                    organisation=self.organisation,
                    type_anomalie='retard',
                    motif=f"Retard de {self.retard} minutes le {self.date_scan.strftime('%d/%m/%Y')} ({self.get_periode_display()})",
                    minutes_manquantes=self.retard,
                    status='en_attente'
                )
                anomalie.save()
                logger.info(f"Anomalie de retard créée pour {self.user.username}")
                
            elif self.depart_anticip > 0:
                # Créer une anomalie de départ anticipé
                anomalie = Anomalie(
                    user=self.user,
                    site=self.site,
                    organisation=self.organisation,
                    type_anomalie='depart_anticipe',
                    motif=f"Départ anticipé de {self.depart_anticip} minutes le {self.date_scan.strftime('%d/%m/%Y')} ({self.get_periode_display()})",
                    minutes_manquantes=self.depart_anticip,
                    status='en_attente'
                )
                anomalie.save()
                logger.info(f"Anomalie de départ anticipé créée pour {self.user.username}")
                
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'anomalie: {str(e)}")
            return False

    @property
    def est_en_retard(self):
        """Indique si le pointage est en retard par rapport au planning"""
        if not self.planning or self.type_pointage != 'ENTREE' or self.periode == 'HORS_PLAGE':
            return False
            
        if self.planning.type != 'FIXE':
            return False
            
        heure_debut = None
        if self.periode == 'MATIN' and self.planning.heure_debut_matin:
            heure_debut = self.planning.heure_debut_matin
        elif self.periode == 'APRES_MIDI' and self.planning.heure_debut_aprem:
            heure_debut = self.planning.heure_debut_aprem
            
        if not heure_debut:
            return False
            
        heure_scan = self.date_scan.time()
        retard_minutes = (
            (heure_scan.hour * 60 + heure_scan.minute) -
            (heure_debut.hour * 60 + heure_debut.minute)
        )
        
        return retard_minutes > self.planning.marge_retard 