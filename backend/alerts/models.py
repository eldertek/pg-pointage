from django.db import models
from django.utils.translation import gettext_lazy as _

class Alert(models.Model):
    """Modèle pour les alertes"""
    
    class AlertType(models.TextChoices):
        LATE = 'LATE', _('Retard')
        EARLY_DEPARTURE = 'EARLY_DEPARTURE', _('Départ anticipé')
        MISSING_ARRIVAL = 'MISSING_ARRIVAL', _('Arrivée manquante')
        MISSING_DEPARTURE = 'MISSING_DEPARTURE', _('Départ manquant')
        INSUFFICIENT_HOURS = 'INSUFFICIENT_HOURS', _('Heures insuffisantes')
        ANOMALY_REPORTED = 'ANOMALY_REPORTED', _('Anomalie signalée')
        OTHER = 'OTHER', _('Autre')
    
    class AlertStatus(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        SENT = 'SENT', _('Envoyé')
        FAILED = 'FAILED', _('Échec')
        RESOLVED = 'RESOLVED', _('Résolu')
    
    employee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('employé')
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('site')
    )
    anomaly = models.ForeignKey(
        'timesheets.Anomaly',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name=_('anomalie')
    )
    alert_type = models.CharField(
        _('type d\'alerte'),
        max_length=20,
        choices=AlertType.choices
    )
    message = models.TextField(_('message'))
    recipients = models.TextField(_('destinataires'), help_text=_('Séparez les emails par des virgules'))
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.PENDING
    )
    sent_at = models.DateTimeField(_('envoyé le'), null=True, blank=True)
    error_message = models.TextField(_('message d\'erreur'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('alerte')
        verbose_name_plural = _('alertes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.employee.get_full_name()} - {self.site.name}"
    
    @property
    def recipient_list(self):
        """Retourne la liste des destinataires"""
        if not self.recipients:
            return []
        return [email.strip() for email in self.recipients.split(',')]

