from django.db import models
from django.utils.translation import gettext_lazy as _

class Report(models.Model):
    """Modèle pour les rapports générés"""
    
    class ReportType(models.TextChoices):
        DAILY = 'DAILY', _('Journalier')
        WEEKLY = 'WEEKLY', _('Hebdomadaire')
        MONTHLY = 'MONTHLY', _('Mensuel')
        CUSTOM = 'CUSTOM', _('Personnalisé')
    
    class ReportFormat(models.TextChoices):
        CSV = 'CSV', _('CSV')
        PDF = 'PDF', _('PDF')
        EXCEL = 'EXCEL', _('Excel')
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('organisation')
    )
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name=_('site')
    )
    name = models.CharField(_('nom'), max_length=100)
    report_type = models.CharField(
        _('type de rapport'),
        max_length=20,
        choices=ReportType.choices,
        default=ReportType.MONTHLY
    )
    report_format = models.CharField(
        _('format de rapport'),
        max_length=20,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF
    )
    start_date = models.DateField(_('date de début'))
    end_date = models.DateField(_('date de fin'))
    file = models.FileField(_('fichier'), upload_to='reports/')
    
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name=_('créé par')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('rapport')
        verbose_name_plural = _('rapports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()} - {self.start_date} à {self.end_date}"

