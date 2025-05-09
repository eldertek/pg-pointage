"""Modèles pour les sites de travail, rattachés à une organisation."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .utils import validate_site_id
from core.utils import is_entity_active


class Site(models.Model):
    """Modèle pour les sites de travail, rattachés à une organisation"""

    name = models.CharField(_('nom'), max_length=100)
    address = models.TextField(_('adresse'))
    postal_code = models.CharField(_('code postal'), max_length=5)
    city = models.CharField(_('ville'), max_length=100)
    country = models.CharField(_('pays'), max_length=100, default='France')
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name=_('organisation'),
        help_text=_('Organisation à laquelle le site est rattaché')
    )
    manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_sites',
        verbose_name=_('manager'),
        help_text=_('Manager responsable du site'),
        limit_choices_to={'role': 'MANAGER'}
    )
    employees = models.ManyToManyField(
        'users.User',
        through='SiteEmployee',
        related_name='sites',
        verbose_name=_('employés'),
        help_text=_('Employés assignés à ce site')
    )
    nfc_id = models.CharField(
        _('ID Site'),
        max_length=10,
        unique=True,
        help_text=_(
            'Format: FFF-Sxxxx où FFF est l\'ID de l\'organisation et xxxx est un nombre entre 0001 et 9999')
    )
    qr_code = models.ImageField(
        _('QR Code'), upload_to='sites/qrcodes/', blank=True, null=True)

    # Paramètres de retard et départ anticipé
    late_margin = models.PositiveIntegerField(
        _('marge de retard (minutes)'), default=15)
    early_departure_margin = models.PositiveIntegerField(
        _('marge de départ anticipé (minutes)'), default=15)
    frequency_tolerance = models.PositiveIntegerField(
        _('tolérance planning fréquence (%)'),
        default=10,
        help_text=_(
            'Pourcentage de tolérance pour la durée des plannings fréquence')
    )
    ambiguous_margin = models.PositiveIntegerField(
        _('marge pour cas ambigus (minutes)'), default=20)

    # Destinataires des alertes
    alert_emails = models.TextField(
        _('emails pour alertes'),
        blank=True,
        help_text=_(
            'Séparez les emails par des virgules. Les alertes seront également envoyées au manager du site.')
    )

    # Paramètres de géolocalisation
    require_geolocation = models.BooleanField(
        _('géolocalisation requise'), default=True)
    geolocation_radius = models.PositiveIntegerField(
        _('rayon de géolocalisation (mètres)'), default=100)

    # Paramètres de synchronisation
    allow_offline_mode = models.BooleanField(
        _('autoriser le mode hors ligne'), default=True)
    max_offline_duration = models.PositiveIntegerField(
        _('durée maximale hors ligne (heures)'), default=24)

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    activation_start_date = models.DateField(
        _('date de début d\'activation'),
        null=True,
        blank=True,
        help_text=_('Date à partir de laquelle le site sera actif')
    )
    activation_end_date = models.DateField(
        _('date de fin d\'activation'),
        null=True,
        blank=True,
        help_text=_('Date à partir de laquelle le site sera inactif')
    )

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

        # Valider que le manager appartient à l'organisation
        if self.manager and self.organization:
            if not self.manager.organizations_set.filter(id=self.organization.id).exists():
                raise ValidationError({
                    'manager': _('Le manager doit appartenir à l\'organisation du site')
                })
            if self.manager.role != 'MANAGER':
                raise ValidationError({
                    'manager': _('L\'utilisateur sélectionné doit avoir le rôle de manager')
                })

    @property
    def alert_email_list(self):
        """Retourne la liste des emails pour les alertes"""
        emails = []
        if self.alert_emails:
            emails.extend([email.strip()
                          for email in str(self.alert_emails).split(',')])
        return list(set(emails))

    @property
    def is_currently_active(self):
        """Détermine si le site est actuellement actif en fonction de son statut et de ses dates d'activation"""
        return is_entity_active(self)


class Schedule(models.Model):
    """Modèle pour les plannings des sites"""

    class ScheduleType(models.TextChoices):
        FIXED = 'FIXED', _('Fixe')
        FREQUENCY = 'FREQUENCY', _('Fréquence')

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
    employees = models.ManyToManyField(
        'users.User',
        through='SiteEmployee',
        related_name='schedules',
        verbose_name=_('employés'),
        help_text=_('Employés assignés à ce planning')
    )

    # Champs pour les plannings de type fréquence
    frequency_tolerance_percentage = models.PositiveSmallIntegerField(
        _('marge de tolérance (%)'),
        null=True,
        blank=True,
        help_text=_(
            'Pourcentage de tolérance pour la durée de présence (plannings fréquence)'),
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    # Champs pour les plannings de type fixe
    late_arrival_margin = models.PositiveSmallIntegerField(
        _('marge de retard (minutes)'),
        null=True,
        blank=True,
        help_text=_('Marge de tolérance pour les retards (plannings fixes)'),
        validators=[MinValueValidator(0)]
    )
    early_departure_margin = models.PositiveSmallIntegerField(
        _('marge de départ anticipé (minutes)'),
        null=True,
        blank=True,
        help_text=_(
            'Marge de tolérance pour les départs anticipés (plannings fixes)'),
        validators=[MinValueValidator(0)]
    )

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    activation_start_date = models.DateField(
        _('date de début d\'activation'),
        null=True,
        blank=True,
        help_text=_('Date à partir de laquelle le planning sera actif')
    )
    activation_end_date = models.DateField(
        _('date de fin d\'activation'),
        null=True,
        blank=True,
        help_text=_('Date à partir de laquelle le planning sera inactif')
    )

    class Meta:
        verbose_name = _('planning')
        verbose_name_plural = _('plannings')
        ordering = ['site']

    def __str__(self):
        return f"Planning {self.schedule_type} - {self.site.name}"

    def clean(self):
        """Validation personnalisée du modèle"""
        super().clean()

        if self.schedule_type == self.ScheduleType.FIXED:
            # Validation des marges pour les plannings fixes
            if self.frequency_tolerance_percentage is not None:
                raise ValidationError({
                    'frequency_tolerance_percentage': _('La marge de tolérance en pourcentage ne doit pas être définie pour un planning fixe')
                })
        else:
            # Validation des marges pour les plannings fréquence
            if any([
                self.late_arrival_margin is not None,
                self.early_departure_margin is not None
            ]):
                raise ValidationError(
                    _('Les marges en minutes ne doivent pas être définies pour un planning fréquence'))


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
    start_time_1 = models.TimeField(
        _('heure de début 1'), null=True, blank=True)
    end_time_1 = models.TimeField(_('heure de fin 1'), null=True, blank=True)
    start_time_2 = models.TimeField(
        _('heure de début 2'), null=True, blank=True)
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
                    raise ValidationError(
                        _('Tous les horaires doivent être définis pour une journée entière'))
            elif self.day_type == self.DayType.AM:
                if not all([self.start_time_1, self.end_time_1]):
                    raise ValidationError(
                        _('Les horaires du matin doivent être définis'))
                if any([self.start_time_2, self.end_time_2]):
                    raise ValidationError(
                        _('Les horaires de l\'après-midi ne doivent pas être définis'))
            else:  # PM
                if not all([self.start_time_2, self.end_time_2]):
                    raise ValidationError(
                        _('Les horaires de l\'après-midi doivent être définis'))
                if any([self.start_time_1, self.end_time_1]):
                    raise ValidationError(
                        _('Les horaires du matin ne doivent pas être définis'))
        else:
            # Pour les plannings fréquence
            if self.frequency_duration is None:
                raise ValidationError({
                    'frequency_duration': _('La durée en minutes doit être définie pour un planning fréquence')
                })
            if any([self.start_time_1, self.end_time_1, self.start_time_2, self.end_time_2]):
                raise ValidationError(
                    _('Les horaires ne doivent pas être définis pour un planning fréquence'))


class SiteEmployee(models.Model):
    """Association entre un site, un employé et un planning"""

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='site_employees',
        verbose_name=_('site')
    )
    employee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='employee_sites',
        verbose_name=_('employé'),
        limit_choices_to={'role': 'EMPLOYEE'}
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_employees',
        verbose_name=_('planning')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)

    class Meta:
        verbose_name = _('employé du site')
        verbose_name_plural = _('employés du site')
        # Suppression de la contrainte d'unicité pour permettre à un employé d'être assigné à plusieurs plannings
        # Un employé peut maintenant être assigné à plusieurs plannings d'un même site
        indexes = [
            models.Index(fields=['schedule', 'is_active']),
            models.Index(fields=['site', 'is_active']),
            models.Index(fields=['site', 'employee', 'schedule']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.site.name}"

    def clean(self):
        """Validation personnalisée du modèle"""
        super().clean()

        # Vérifier que l'employé appartient à l'organisation du site
        if self.employee and self.site and not self.employee.organizations_set.filter(id=self.site.organization.id).exists():
            raise ValidationError({
                'employee': _('L\'employé doit appartenir à l\'organisation du site')
            })
