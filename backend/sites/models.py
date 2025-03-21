from django.db import models
from django.utils.translation import gettext_lazy as _

class Site(models.Model):
    """Modèle pour les sites de travail"""
    
    name = models.CharField(_('nom'), max_length=100)
    address = models.TextField(_('adresse'))
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name=_('organisation')
    )
    nfc_id = models.CharField(_('ID NFC'), max_length=100, unique=True)
    qr_code = models.ImageField(_('QR Code'), upload_to='sites/qrcodes/', blank=True, null=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Paramètres de retard et départ anticipé
    late_margin = models.PositiveIntegerField(_('marge de retard (minutes)'), default=15)
    early_departure_margin = models.PositiveIntegerField(_('marge de départ anticipé (minutes)'), default=15)
    
    # Destinataires des alertes
    alert_emails = models.TextField(_('emails pour alertes'), blank=True, help_text=_('Séparez les emails par des virgules'))
    
    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
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
        unique_together = ['site', 'employee']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.site.name}"

