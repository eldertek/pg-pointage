from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .utils import generate_user_id, validate_user_id

class User(AbstractUser):
    """Modèle utilisateur personnalisé avec relation ManyToMany vers les organisations"""

    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        EMPLOYEE = 'EMPLOYEE', _('Employé')

    class ScanPreference(models.TextChoices):
        BOTH = 'BOTH', _('NFC et QR Code')
        NFC_ONLY = 'NFC_ONLY', _('NFC uniquement')
        QR_ONLY = 'QR_ONLY', _('QR Code uniquement')

    class Language(models.TextChoices):
        FRENCH = 'fr', _('Français')
        ENGLISH = 'en', _('Anglais')

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
    simplified_mobile_view = models.BooleanField(
        default=False,
        help_text=_('Si activé, affiche uniquement le bouton de pointage sur mobile')
    )
    language = models.CharField(
        _('langue'),
        max_length=2,
        choices=Language.choices,
        default=Language.FRENCH,
        help_text=_('Langue préférée de l\'utilisateur')
    )
    organizations = models.ManyToManyField(
        'organizations.Organization',
        related_name='users',
        verbose_name=_('organisations'),
        help_text=_('Organisations auxquelles l\'utilisateur est rattaché')
    )
    phone_number = models.CharField(_('numéro de téléphone'), max_length=15, blank=True)
    is_active = models.BooleanField(_('actif'), default=True)

    # ID unique pour chaque utilisateur
    employee_id = models.CharField(
        _('ID employé'),
        max_length=6,
        blank=True,
        unique=True,
        help_text=_('ID unique de l\'utilisateur au format UXXXXX')
    )

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
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    def has_organization_permission(self, organization):
        """Vérifie si l'utilisateur a des permissions sur une organisation"""
        if self.is_super_admin:
            return True
        return self.organizations.filter(id=organization.id).exists()

    def save(self, *args, **kwargs):
        # Générer un ID utilisateur unique au format UXXXXX si vide
        if not self.employee_id:
            self.employee_id = generate_user_id()

        # Valider le format de l'ID utilisateur
        if self.employee_id and not validate_user_id(self.employee_id):
            # Si l'ID n'est pas valide, en générer un nouveau
            self.employee_id = generate_user_id()

        super().save(*args, **kwargs)

