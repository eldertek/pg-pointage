from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
import logging
from django.utils import timezone

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler pour la console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class OrganisationModel(models.Model):
    """
    Classe de base pour les modèles liés à une organisation
    Ajoute des champs utiles comme organisation, created_at, updated_at
    """
    organisation = models.ForeignKey(
        'auth.Group',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name="Organisation",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=False,
        default=timezone.now,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de dernière modification"
    )
    
    class Meta:
        abstract = True 