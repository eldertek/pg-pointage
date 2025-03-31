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
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_sites',
        verbose_name=_('manager'),
        limit_choices_to={'role': 'MANAGER'}
    )
    nfc_id = models.CharField(
        _('ID Site'), 
        max_length=10,
        unique=True,
        help_text=_('Format: FFF-Sxxxx où FFF est l\'ID de l\'organisation et xxxx est un nombre entre 0001 et 9999')
    )
    qr_code = models.ImageField(_('QR Code'), upload_to='sites/qrcodes/', blank=True, null=True)
    
    # Paramètres de retard et départ anticipé
    late_margin = models.PositiveIntegerField(_('marge de retard (minutes)'), default=15)
    early_departure_margin = models.PositiveIntegerField(_('marge de départ anticipé (minutes)'), default=15)
    frequency_tolerance = models.PositiveIntegerField(
        _('tolérance planning fréquence (%)'),
        default=10,
        help_text=_('Pourcentage de tolérance pour la durée des plannings fréquence')
    )
    ambiguous_margin = models.PositiveIntegerField(_('marge pour cas ambigus (minutes)'), default=20)
    
    # Destinataires des alertes
    alert_emails = models.TextField(
        _('emails pour alertes'), 
        blank=True, 
        help_text=_('Séparez les emails par des virgules. Les alertes seront également envoyées au manager du site.')
    )
    
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
                'nfc_id': _('L\'ID du site doit être au format FFF-Sxxxx')
            })
        
        # Valider que le manager appartient à la même organisation
        if self.manager and self.organization and self.manager.organization != self.organization:
            raise ValidationError({
                'manager': _('Le manager doit appartenir à la même organisation que le site')
            })
    
    @property
    def alert_email_list(self):
        """Retourne la liste des emails pour les alertes, incluant le manager"""
        emails = []
        if self.alert_emails:
            emails.extend([email.strip() for email in self.alert_emails.split(',')])
        if self.manager and self.manager.email:
            emails.append(self.manager.email)
        return list(set(emails))  # Dédupliquer les emails


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
    schedule_type = models.CharField(
        _('type de planning'),
        max_length=20,
        choices=ScheduleType.choices,
        default=ScheduleType.FIXED
    )
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('planning')
        verbose_name_plural = _('plannings')
        ordering = ['site']
    
    def __str__(self):
        return f"Planning {self.schedule_type} - {self.site.name}"


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
    
    class DayType(models.TextChoices):
        FULL = 'FULL', _('Journée entière')
        AM = 'AM', _('Matin')
        PM = 'PM', _('Après-midi')
    
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
    day_type = models.CharField(
        _('type de journée'),
        max_length=4,
        choices=DayType.choices,
        default=DayType.FULL
    )
    start_time_1 = models.TimeField(_('heure de début 1'), null=True, blank=True)
    end_time_1 = models.TimeField(_('heure de fin 1'), null=True, blank=True)
    start_time_2 = models.TimeField(_('heure de début 2'), null=True, blank=True)
    end_time_2 = models.TimeField(_('heure de fin 2'), null=True, blank=True)
    frequency_duration = models.PositiveIntegerField(
        _('durée en minutes'),
        null=True,
        blank=True,
        help_text=_('Pour les plannings de type fréquence uniquement')
    )
    
    class Meta:
        verbose_name = _('détail du planning')
        verbose_name_plural = _('détails des plannings')
        ordering = ['schedule', 'day_of_week']
        unique_together = ['schedule', 'day_of_week']
    
    def __str__(self):
        day_name = self.get_day_of_week_display()
        return f"Planning {self.schedule.schedule_type} - {self.schedule.site.name} - {day_name}"
    
    def clean(self):
        """Validation personnalisée du modèle"""
        super().clean()
        
        if self.schedule.schedule_type == Schedule.ScheduleType.FIXED:
            # Pour les plannings fixes
            if self.frequency_duration is not None:
                raise ValidationError({
                    'frequency_duration': _('La durée en minutes ne doit pas être définie pour un planning fixe')
                })
                
            if self.day_type == self.DayType.FULL:
                if not all([self.start_time_1, self.end_time_1, self.start_time_2, self.end_time_2]):
                    raise ValidationError(_('Tous les horaires doivent être définis pour une journée entière'))
            elif self.day_type == self.DayType.AM:
                if not all([self.start_time_1, self.end_time_1]):
                    raise ValidationError(_('Les horaires du matin doivent être définis'))
                if any([self.start_time_2, self.end_time_2]):
                    raise ValidationError(_('Les horaires de l\'après-midi ne doivent pas être définis'))
            else:  # PM
                if not all([self.start_time_2, self.end_time_2]):
                    raise ValidationError(_('Les horaires de l\'après-midi doivent être définis'))
                if any([self.start_time_1, self.end_time_1]):
                    raise ValidationError(_('Les horaires du matin ne doivent pas être définis'))
        else:
            # Pour les plannings fréquence
            if self.frequency_duration is None:
                raise ValidationError({
                    'frequency_duration': _('La durée en minutes doit être définie pour un planning fréquence')
                })
            if any([self.start_time_1, self.end_time_1, self.start_time_2, self.end_time_2]):
                raise ValidationError(_('Les horaires ne doivent pas être définis pour un planning fréquence'))


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
        verbose_name=_('planning'),
        db_index=True
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('employé du site')
        verbose_name_plural = _('employés du site')
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'employee'],
                name='unique_site_employee'
            )
        ]
        indexes = [
            models.Index(fields=['schedule', 'is_active']),
            models.Index(fields=['site', 'is_active'])
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.site.name}"

