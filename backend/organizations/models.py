from django.db import models
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    """Modèle pour les franchises/organisations"""
    
    name = models.CharField(_('nom'), max_length=100)
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
        return self.name

