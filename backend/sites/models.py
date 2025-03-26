from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .utils import validate_site_id

class Site(models.Model):
    """Modèle pour les sites de travail"""
    
    name = models.CharField(_('nom'), max_length=100)
    address = models.TextField(_('adresse'))
    postal_code = models.CharField(_('code postal'), max_length=5)
    city = models.CharField(_('ville'), max_length=100)
    country = models.CharField(_('pays'), max_length=100, default='France')
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name=_('organisation')
    )
    nfc_id = models.CharField(
        _('ID Site'), 
        max_length=5,
        unique=True,
        help_text=_('Format: S0001 à S9999')
    )
    qr_code = models.ImageField(_('QR Code'), upload_to='sites/qrcodes/', blank=True, null=True)
    
    # Paramètres de retard et départ anticipé
    late_margin = models.PositiveIntegerField(_('marge de retard (minutes)'), default=15)
    early_departure_margin = models.PositiveIntegerField(_('marge de départ anticipé (minutes)'), default=15)
    ambiguous_margin = models.PositiveIntegerField(_('marge pour cas ambigus (minutes)'), default=20)
    
    # Destinataires des alertes
    alert_emails = models.TextField(_('emails pour alertes'), blank=True, help_text=_('Séparez les emails par des virgules'))
    
    # Paramètres de géolocalisation
    require_geolocation = models.BooleanField(_('géolocalisation requise'), default=True)
    geolocation_radius = models.PositiveIntegerField(_('rayon de géolocalisation (mètres)'), default=100)
    
    # Paramètres de synchronisation
    allow_offline_mode = models.BooleanField(_('autoriser le mode hors ligne'), default=True)
    max_offline_duration = models.PositiveIntegerField(_('durée maximale hors ligne (heures)'), default=24)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    def clean(self):
        """Validation personnalisée du modèle"""
        super().clean()
        
        # Valider le format de l'ID du site
        if self.nfc_id and not validate_site_id(self.nfc_id):
            raise ValidationError({
                'nfc_id': _('L\'ID du site doit être au format S0001 à S9999')
            })
    
    @property
    def alert_email_list(self):
        """Retourne la liste des emails pour les alertes"""
        if not self.alert_emails:
            return []
        return [email.strip() for email in self.alert_emails.split(',')]


class Schedule(models.Model):
    """Modèle pour les plannings des sites"""
    
    class ScheduleType(models.TextChoices):
        FIXED = 'FIXED', _('Fixe (gardien)')
        FREQUENCY = 'FREQUENCY', _('Fréquence (nettoyage)')
    
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('site')
    )
    name = models.CharField(_('nom'), max_length=100)
    schedule_type = models.CharField(
        _('type de planning'),
        max_length=20,
        choices=ScheduleType.choices,
        default=ScheduleType.FIXED
    )
    
    # Pour les plannings de type FREQUENCY
    min_daily_hours = models.DecimalField(
        _('heures minimales par jour'),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True
    )
    min_weekly_hours = models.DecimalField(
        _('heures minimales par semaine'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Paramètres de flexibilité
    allow_early_arrival = models.BooleanField(_('autoriser arrivée en avance'), default=True)
    allow_late_departure = models.BooleanField(_('autoriser départ tardif'), default=True)
    early_arrival_limit = models.PositiveIntegerField(_('limite arrivée en avance (minutes)'), default=30)
    late_departure_limit = models.PositiveIntegerField(_('limite départ tardif (minutes)'), default=30)
    
    # Paramètres de pause
    break_duration = models.PositiveIntegerField(_('durée de pause (minutes)'), default=60)
    min_break_start = models.TimeField(_('début pause au plus tôt'), null=True, blank=True)
    max_break_end = models.TimeField(_('fin pause au plus tard'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('planning')
        verbose_name_plural = _('plannings')
        ordering = ['site', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.site.name}"


class ScheduleDetail(models.Model):
    """Détails des plannings pour les horaires fixes"""
    
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, _('Lundi')
        TUESDAY = 1, _('Mardi')
        WEDNESDAY = 2, _('Mercredi')
        THURSDAY = 3, _('Jeudi')
        FRIDAY = 4, _('Vendredi')
        SATURDAY = 5, _('Samedi')
        SUNDAY = 6, _('Dimanche')
    
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_('planning')
    )
    day_of_week = models.IntegerField(
        _('jour de la semaine'),
        choices=DayOfWeek.choices
    )
    start_time_1 = models.TimeField(_('heure de début 1'))
    end_time_1 = models.TimeField(_('heure de fin 1'))
    start_time_2 = models.TimeField(_('heure de début 2'), null=True, blank=True)
    end_time_2 = models.TimeField(_('heure de fin 2'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('détail du planning')
        verbose_name_plural = _('détails des plannings')
        ordering = ['schedule', 'day_of_week']
        unique_together = ['schedule', 'day_of_week']
    
    def __str__(self):
        day_name = self.get_day_of_week_display()
        return f"{self.schedule.name} - {day_name}"


class SiteEmployee(models.Model):
    """Association entre un site et un employé"""
    
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name=_('site')
    )
    employee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='assigned_sites',
        verbose_name=_('employé')
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_employees',
        verbose_name=_('planning')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('employé du site')
        verbose_name_plural = _('employés du site')
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'employee', 'schedule'],
                condition=models.Q(is_active=True),
                name='unique_active_site_employee_schedule'
            )
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.site.name}"

