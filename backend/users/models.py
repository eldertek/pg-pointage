from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
        MANAGER = 'MANAGER', _('Manager')
        EMPLOYEE = 'EMPLOYEE', _('Employé')
    
    class ScanPreference(models.TextChoices):
        BOTH = 'BOTH', _('NFC et QR Code')
        NFC_ONLY = 'NFC_ONLY', _('NFC uniquement')
        QR_ONLY = 'QR_ONLY', _('QR Code uniquement')
    
    email = models.EmailField(_('adresse email'), unique=True)
    role = models.CharField(
        _('rôle'),
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE
    )
    scan_preference = models.CharField(
        _('préférence de scan'),
        max_length=20,
        choices=ScanPreference.choices,
        default=ScanPreference.BOTH,
        blank=True,
        null=True,
        help_text=_('Uniquement pour les employés')
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('organisation')
    )
    phone_number = models.CharField(_('numéro de téléphone'), max_length=15, blank=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Pour les employés
    employee_id = models.CharField(_('ID employé'), max_length=50, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN
    
    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER
    
    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

