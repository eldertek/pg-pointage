from django.db import models
from .base import OrganisationModel

class Site(OrganisationModel):
    """
    Modèle représentant un site physique où les utilisateurs peuvent pointer
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du site"
    )
    qr_code_value = models.CharField(
        max_length=100,
        verbose_name="Valeur du QR Code"
    )
    emails_alertes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Emails pour les alertes",
        help_text="Liste d'emails séparés par des virgules pour les notifications"
    )
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adresse du site"
    )

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['name']
        unique_together = [
            ('name', 'organisation'),
            ('qr_code_value', 'organisation')
        ]

    def __str__(self):
        org_name = self.organisation.name if self.organisation else "-"
        return f"{self.name} - {org_name}"

    def get_email_list(self):
        """
        Retourne la liste des emails pour les alertes
        """
        if not self.emails_alertes:
            return []
        return [email.strip() for email in self.emails_alertes.split(',') if email.strip()] 