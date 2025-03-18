from django.contrib.auth.models import AbstractUser
from django.db import models
from .base import OrganisationModel

class User(AbstractUser, OrganisationModel):
    """
    Modèle utilisateur personnalisé avec gestion des rôles
    """
    ROLE_CHOICES = (
        ('gardien', 'Gardien'),
        ('agent_de_nettoyage', 'Agent de nettoyage'),
        ('manager', 'Manager'),
    )
    
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='gardien',
        help_text="Rôle de l'utilisateur dans l'application"
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['username']

    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"{self.username} ({self.role}) - {org_name}"

    def save(self, *args, **kwargs):
        # Assurez-vous que l'utilisateur a les permissions appropriées selon son rôle
        if self.role == 'manager':
            self.is_staff = True
        super().save(*args, **kwargs) 