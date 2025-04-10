"""Modèle pour les pointages"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError


class Timesheet(models.Model):
    """Modèle pour les pointages"""

    class EntryType(models.TextChoices):
        ARRIVAL = 'ARRIVAL', _('Arrivée')
        DEPARTURE = 'DEPARTURE', _('Départ')

    class ScanType(models.TextChoices):
        NFC = 'NFC', _('NFC')
        QR_CODE = 'QR_CODE', _('QR Code')

    employee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='timesheets',
        verbose_name=_('employé')
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.CASCADE,
        related_name='timesheets',
        verbose_name=_('site')
    )
    timestamp = models.DateTimeField(_('horodatage'), default=timezone.now)
    entry_type = models.CharField(
        _('type d\'entrée'),
        max_length=20,
        choices=EntryType.choices
    )
    scan_type = models.CharField(
        _('type de scan'),
        max_length=10,
        choices=ScanType.choices,
        default=ScanType.QR_CODE
    )

    # Informations de géolocalisation
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=12,
        decimal_places=10,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=12,
        decimal_places=10,
        null=True,
        blank=True
    )

    # Informations sur le retard ou départ anticipé
    is_late = models.BooleanField(_('en retard'), default=False)
    late_minutes = models.PositiveIntegerField(
        _('minutes de retard'), default=0)
    is_early_departure = models.BooleanField(
        _('départ anticipé'), default=False)
    early_departure_minutes = models.PositiveIntegerField(
        _('minutes de départ anticipé'), default=0)

    # Informations sur le pointage hors planning
    is_out_of_schedule = models.BooleanField(_('hors planning'), default=False)
    is_ambiguous = models.BooleanField(_('pointage ambigu'), default=False)

    # Informations sur la synchronisation
    created_offline = models.BooleanField(_('créé hors ligne'), default=False)
    synced_at = models.DateTimeField(
        _('synchronisé le'), null=True, blank=True)

    # Informations sur la géolocalisation
    geolocation_enabled = models.BooleanField(
        _('géolocalisation activée'), default=True)

    # Informations sur la correction manuelle
    corrected_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrected_timesheets',
        verbose_name=_('corrigé par')
    )
    correction_note = models.TextField(_('note de correction'), blank=True)
    correction_date = models.DateTimeField(
        _('date de correction'), null=True, blank=True)

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)

    def clean(self):
        # Vérifier s'il existe déjà un pointage du même type pour le même employé et site
        last_timesheet = Timesheet.objects.filter(
            employee=self.employee,
            site=self.site,
            timestamp__date=timezone.localtime(self.timestamp).date()
        ).exclude(id=self.id).order_by('-timestamp').first()

        if last_timesheet and last_timesheet.entry_type == self.entry_type:
            # On ne crée pas d'anomalie ici pour éviter les problèmes avec les objets non sauvegardés
            # L'anomalie sera créée dans la méthode create_consecutive_anomaly après la sauvegarde
            self._create_consecutive_anomaly = True
            self._last_timesheet = last_timesheet

            if self.entry_type == self.EntryType.ARRIVAL:
                raise ValidationError({
                    'entry_type': _('Vous avez déjà pointé votre arrivée. Vous devez d\'abord pointer votre départ.')
                })
            else:
                raise ValidationError({
                    'entry_type': _('Vous avez déjà pointé votre départ. Vous devez d\'abord pointer votre arrivée.')
                })

        # Vérifier la cohérence arrivée/départ
        if last_timesheet:
            if self.entry_type == self.EntryType.ARRIVAL and last_timesheet.entry_type == self.EntryType.ARRIVAL:
                raise ValidationError({
                    'entry_type': _('Vous devez d\'abord pointer votre départ avant de pointer une nouvelle arrivée.')
                })
            elif self.entry_type == self.EntryType.DEPARTURE and last_timesheet.entry_type == self.EntryType.DEPARTURE:
                raise ValidationError({
                    'entry_type': _('Vous devez d\'abord pointer votre arrivée avant de pointer un nouveau départ.')
                })

    def create_consecutive_anomaly(self):
        """Crée une anomalie pour les pointages consécutifs du même type"""
        if hasattr(self, '_create_consecutive_anomaly') and self._create_consecutive_anomaly:
            last_timesheet = self._last_timesheet
            Anomaly.objects.create(
                employee=self.employee,
                site=self.site,
                timesheet=self,
                date=timezone.localtime(self.timestamp).date(),
                anomaly_type=Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE,
                description=_(
                    f'Pointage {self.get_entry_type_display()} consécutif détecté. '
                    f'Dernier pointage : {last_timesheet.timestamp.strftime("%H:%M")}'
                ),
                status=Anomaly.AnomalyStatus.PENDING
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Créer l'anomalie après la sauvegarde
        self.create_consecutive_anomaly()

    class Meta:
        verbose_name = _('pointage')
        verbose_name_plural = _('pointages')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.site.name} - {self.timestamp}"


class Anomaly(models.Model):
    """Modèle pour les anomalies de pointage"""

    class AnomalyType(models.TextChoices):
        LATE = 'LATE', _('Retard')
        EARLY_DEPARTURE = 'EARLY_DEPARTURE', _('Départ anticipé')
        MISSING_ARRIVAL = 'MISSING_ARRIVAL', _('Arrivée manquante')
        MISSING_DEPARTURE = 'MISSING_DEPARTURE', _('Départ manquant')
        INSUFFICIENT_HOURS = 'INSUFFICIENT_HOURS', _('Heures insuffisantes')
        CONSECUTIVE_SAME_TYPE = 'CONSECUTIVE_SAME_TYPE', _(
            'Pointages consécutifs du même type')
        OTHER = 'OTHER', _('Autre')

    class AnomalyStatus(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        RESOLVED = 'RESOLVED', _('Résolu')
        IGNORED = 'IGNORED', _('Ignoré')

    employee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='anomalies',
        verbose_name=_('employé')
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.CASCADE,
        related_name='anomalies',
        verbose_name=_('site')
    )
    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anomalies',
        verbose_name=_('pointage')
    )
    date = models.DateField(_('date'))
    anomaly_type = models.CharField(
        _('type d\'anomalie'),
        max_length=30,
        choices=AnomalyType.choices
    )
    description = models.TextField(_('description'), blank=True)
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=AnomalyStatus.choices,
        default=AnomalyStatus.PENDING
    )

    # Pour les retards et départs anticipés
    minutes = models.PositiveIntegerField(_('minutes'), default=0)

    # Pour les corrections manuelles
    corrected_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrected_anomalies',
        verbose_name=_('corrigé par')
    )
    correction_date = models.DateTimeField(
        _('date de correction'), null=True, blank=True)
    correction_note = models.TextField(_('note de correction'), blank=True)

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('anomalie')
        verbose_name_plural = _('anomalies')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.site.name} - {self.date} - {self.get_anomaly_type_display()}"


class EmployeeReport(models.Model):
    """Modèle pour les rapports d'employés"""

    employee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='employee_reports',
        verbose_name=_('employé')
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.CASCADE,
        related_name='employee_reports',
        verbose_name=_('site')
    )
    start_date = models.DateField(_('date de début'))
    end_date = models.DateField(_('date de fin'))

    # Statistiques
    total_hours = models.DecimalField(
        _('total des heures'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    late_count = models.PositiveIntegerField(_('nombre de retards'), default=0)
    total_late_minutes = models.PositiveIntegerField(
        _('minutes totales de retard'), default=0)
    early_departure_count = models.PositiveIntegerField(
        _('nombre de départs anticipés'), default=0)
    total_early_departure_minutes = models.PositiveIntegerField(
        _('minutes totales de départ anticipé'), default=0)
    anomaly_count = models.PositiveIntegerField(
        _('nombre d\'anomalies'), default=0)

    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('rapport d\'employé')
        verbose_name_plural = _('rapports d\'employés')
        ordering = ['-created_at']

    def __str__(self):
        return f"Rapport de {self.employee.get_full_name()} - {self.start_date} à {self.end_date}"
