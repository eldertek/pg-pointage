from django.db import models
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    """Modèle pour les franchises/organisations"""
    
    name = models.CharField(_('nom'), max_length=100)
    address = models.TextField(_('adresse'), blank=True)
    phone = models.CharField(_('téléphone'), max_length=15, blank=True)
    email = models.EmailField(_('email'), blank=True)
    logo = models.ImageField(_('logo'), upload_to='organizations/logos/', blank=True, null=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('organisation')
        verbose_name_plural = _('organisations')
        ordering = ['name']
    
    def __str__(self):
        return self.name

