from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class Organization(models.Model):
    """Modèle pour les organisations - Entité centrale qui relie utilisateurs, sites et plannings"""
    
    name = models.CharField(_('nom'), max_length=100)
    org_id = models.CharField(
        _('ID Organisation'),
        max_length=4,
        unique=True,
        help_text=_('ID unique de l\'organisation au format O + 3 chiffres')
    )
    address = models.TextField(_('adresse'), blank=True)
    postal_code = models.CharField(_('code postal'), max_length=5, blank=True)
    city = models.CharField(_('ville'), max_length=100, blank=True)
    country = models.CharField(_('pays'), max_length=100, default='France')
    phone = models.CharField(_('téléphone'), max_length=15, blank=True)
    email = models.EmailField(_('email'), blank=True)
    contact_email = models.EmailField(_('email de contact'), blank=True)
    siret = models.CharField(_('SIRET'), max_length=14, blank=True)
    logo = models.ImageField(_('logo'), upload_to='organizations/logos/', blank=True, null=True)
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('organisation')
        verbose_name_plural = _('organisations')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.org_id})"
    
    def clean(self):
        """Validation personnalisée du modèle"""
        super().clean()
        
        # Valider le format de l'ID de l'organisation
        if self.org_id:
            if not self.org_id.startswith('O'):
                raise ValidationError({
                    'org_id': _('L\'ID de l\'organisation doit commencer par O')
                })
            try:
                number = int(self.org_id[1:])
                if not (0 <= number <= 999):
                    raise ValidationError({
                        'org_id': _('L\'ID de l\'organisation doit être au format O + nombre entre 000 et 999')
                    })
            except ValueError:
                raise ValidationError({
                    'org_id': _('L\'ID de l\'organisation doit être au format O + 3 chiffres')
                })
    
    def save(self, *args, **kwargs):
        # Si pas d'org_id, en générer un
        if not self.org_id and not Organization.objects.filter(id=self.id).exists():
            with transaction.atomic():
                # Trouver le dernier ID utilisé
                last_org = Organization.objects.select_for_update().order_by('-org_id').first()
                if last_org and last_org.org_id:
                    try:
                        next_number = int(last_org.org_id[1:]) + 1
                        if next_number > 999:
                            next_number = 1
                    except ValueError:
                        next_number = 1
                else:
                    next_number = 1
                self.org_id = f"O{next_number:03d}"
        
        super().save(*args, **kwargs)

    def get_total_anomalies(self):
        """Retourne le nombre total d'anomalies pour l'organisation"""
        from timesheets.models import TimesheetAnomaly
        return TimesheetAnomaly.objects.filter(
            timesheet__user__organizations=self
        ).count()
        
    def get_pending_anomalies(self):
        """Retourne le nombre d'anomalies en attente pour l'organisation"""
        from timesheets.models import TimesheetAnomaly
        return TimesheetAnomaly.objects.filter(
            timesheet__user__organizations=self,
            status='PENDING'
        ).count()

