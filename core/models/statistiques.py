from django.db import models
from django.utils import timezone
import logging
from .base import OrganisationModel

logger = logging.getLogger(__name__)

class StatistiquesTemps(OrganisationModel):
    """
    Modèle pour les statistiques de temps de travail des utilisateurs par site
    """
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='statistiques',
        verbose_name="Utilisateur"
    )
    site = models.ForeignKey(
        'Site',
        on_delete=models.CASCADE,
        related_name='statistiques',
        verbose_name="Site"
    )
    mois = models.PositiveSmallIntegerField(
        verbose_name="Mois"
    )
    annee = models.PositiveSmallIntegerField(
        verbose_name="Année"
    )
    minutes_travaillees = models.PositiveIntegerField(
        default=0,
        verbose_name="Minutes travaillées"
    )
    minutes_retard = models.PositiveIntegerField(
        default=0,
        verbose_name="Minutes de retard"
    )
    minutes_depart_anticipe = models.PositiveIntegerField(
        default=0,
        verbose_name="Minutes de départ anticipé"
    )
    minutes_absence = models.PositiveIntegerField(
        default=0,
        verbose_name="Minutes d'absence"
    )
    jours_travailles = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Jours travaillés"
    )
    date_derniere_maj = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de dernière mise à jour"
    )
    
    class Meta:
        verbose_name = "Statistiques de temps"
        verbose_name_plural = "Statistiques de temps"
        ordering = ['-annee', '-mois']
        unique_together = ('user', 'site', 'mois', 'annee')
        indexes = [
            models.Index(fields=['user', 'annee', 'mois']),
            models.Index(fields=['site', 'annee', 'mois']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.site.name} - {self.mois}/{self.annee}"
        
    @property
    def minutes_manquantes_total(self):
        """Calcule le total des minutes manquantes"""
        return self.minutes_retard + self.minutes_depart_anticipe + self.minutes_absence
        
    @property
    def heures_manquantes(self):
        """Convertit les minutes manquantes en heures pour affichage"""
        return round(self.minutes_manquantes_total / 60, 2)
        
    @classmethod
    def update_from_anomalies(cls, user_id, site_id, date=None):
        """
        Met à jour les statistiques pour un utilisateur et un site à partir des anomalies
        """
        if not date:
            date = timezone.now()
            
        # Importer ici pour éviter les références circulaires
        from .anomalie import Anomalie
        from .user import User
        from .site import Site
        
        try:
            user = User.objects.get(id=user_id)
            site = Site.objects.get(id=site_id)
            
            # Récupérer ou créer les statistiques pour ce mois
            stats, created = cls.objects.get_or_create(
                user=user,
                site=site,
                organisation=user.organisation or site.organisation,
                mois=date.month,
                annee=date.year
            )
            
            # Réinitialiser les compteurs liés aux anomalies
            stats.minutes_retard = 0
            stats.minutes_depart_anticipe = 0
            stats.minutes_absence = 0
            
            # Récupérer toutes les anomalies du mois pour cet utilisateur et ce site
            debut_mois = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                fin_mois = date.replace(year=date.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(seconds=1)
            else:
                fin_mois = date.replace(month=date.month+1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(seconds=1)
                
            # Filtrer les anomalies non justifiées
            anomalies = Anomalie.objects.filter(
                user=user,
                site=site,
                date_creation__gte=debut_mois,
                date_creation__lte=fin_mois,
                status__in=['en_attente', 'non_justifiee', 'en_cours']
            )
            
            # Mettre à jour les statistiques à partir des anomalies
            for anomalie in anomalies:
                if anomalie.type_anomalie == 'retard':
                    stats.minutes_retard += anomalie.minutes_manquantes
                elif anomalie.type_anomalie == 'depart_anticipe':
                    stats.minutes_depart_anticipe += anomalie.minutes_manquantes
                elif anomalie.type_anomalie == 'absence':
                    stats.minutes_absence += anomalie.minutes_manquantes
                    
            # Sauvegarder les statistiques sans déclencher la récursion
            stats.save()
            
            logger.info(f"Statistiques mises à jour pour {user.username} sur {site.name} ({date.month}/{date.year})")
            return stats
            
        except User.DoesNotExist:
            logger.error(f"Utilisateur avec ID {user_id} non trouvé")
        except Site.DoesNotExist:
            logger.error(f"Site avec ID {site_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {str(e)}")
            
        return None
        
    @classmethod
    def update_from_pointages(cls, user_id, site_id, date=None):
        """
        Met à jour les statistiques pour un utilisateur et un site à partir des pointages
        """
        if not date:
            date = timezone.now()
            
        # Importer ici pour éviter les références circulaires
        from .pointage import Pointage
        from .user import User
        from .site import Site
        
        try:
            user = User.objects.get(id=user_id)
            site = Site.objects.get(id=site_id)
            
            # Récupérer ou créer les statistiques pour ce mois
            stats, created = cls.objects.get_or_create(
                user=user,
                site=site,
                organisation=user.organisation or site.organisation,
                mois=date.month,
                annee=date.year
            )
            
            # Récupérer tous les pointages du mois pour cet utilisateur et ce site
            debut_mois = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                fin_mois = date.replace(year=date.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(seconds=1)
            else:
                fin_mois = date.replace(month=date.month+1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(seconds=1)
                
            # Calculer les jours travaillés
            jours_travailles = Pointage.objects.filter(
                user=user,
                site=site,
                date_scan__gte=debut_mois,
                date_scan__lte=fin_mois
            ).dates('date_scan', 'day').distinct().count()
            
            stats.jours_travailles = jours_travailles
            
            # Calculer les minutes travaillées
            # Pour cela, nous avons besoin de trouver les paires entrée/sortie
            pointages = Pointage.objects.filter(
                user=user,
                site=site,
                date_scan__gte=debut_mois,
                date_scan__lte=fin_mois
            ).order_by('date_scan')
            
            # Réinitialiser le compteur
            stats.minutes_travaillees = 0
            
            # Variables pour le calcul
            dernier_entree = None
            
            # Parcourir tous les pointages pour calculer les durées
            for pointage in pointages:
                if pointage.type_pointage == 'ENTREE':
                    dernier_entree = pointage
                elif pointage.type_pointage == 'SORTIE' and dernier_entree:
                    # Calculer la durée entre l'entrée et la sortie
                    duree = pointage.date_scan - dernier_entree.date_scan
                    minutes = int(duree.total_seconds() / 60)
                    stats.minutes_travaillees += minutes
                    dernier_entree = None
            
            # Sauvegarder les statistiques
            stats.save()
            
            logger.info(f"Statistiques de pointage mises à jour pour {user.username} sur {site.name} ({date.month}/{date.year})")
            return stats
            
        except User.DoesNotExist:
            logger.error(f"Utilisateur avec ID {user_id} non trouvé")
        except Site.DoesNotExist:
            logger.error(f"Site avec ID {site_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques de pointage: {str(e)}")
            
        return None
        
    @property
    def heures_travaillees(self):
        """
        Retourne le nombre d'heures travaillées formaté
        """
        heures = self.minutes_travaillees // 60
        minutes = self.minutes_travaillees % 60
        return f"{heures}h{minutes:02d}"
        
    @property
    def heures_retard(self):
        """
        Retourne le nombre d'heures de retard formaté
        """
        heures = self.minutes_retard // 60
        minutes = self.minutes_retard % 60
        return f"{heures}h{minutes:02d}"
        
    @property
    def heures_depart_anticipe(self):
        """
        Retourne le nombre d'heures de départ anticipé formaté
        """
        heures = self.minutes_depart_anticipe // 60
        minutes = self.minutes_depart_anticipe % 60
        return f"{heures}h{minutes:02d}"
        
    @property
    def heures_absence(self):
        """
        Retourne le nombre d'heures d'absence formaté
        """
        heures = self.minutes_absence // 60
        minutes = self.minutes_absence % 60
        return f"{heures}h{minutes:02d}"

    def clean(self):
        """Validation du modèle"""
        from django.core.exceptions import ValidationError
        
        # Vérifier la cohérence de l'organisation
        if self.organisation:
            if (self.user.organisation and self.user.organisation != self.organisation) or \
               (self.site.organisation and self.site.organisation != self.organisation):
                raise ValidationError("L'utilisateur et le site doivent appartenir à la même organisation que les statistiques.") 