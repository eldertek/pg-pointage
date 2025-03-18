from rest_framework import serializers
from .models import Pointage, Anomalie, Site, Planning, User
from django.utils import timezone
from zoneinfo import ZoneInfo
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle User, afin d'exposer les informations pertinentes des utilisateurs.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']  # Inclure les champs nécessaires


class SiteSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Site, utilisé pour exposer les informations des sites.
    """
    class Meta:
        model = Site
        fields = ['id', 'name', 'qr_code_value', 'marge_retard', 'marge_depart_anticip', 'emails_alertes']


class PlanningSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Planning, utilisé pour exposer les informations liées aux plannings des sites.
    """
    site = SiteSerializer(read_only=True)  # Inclure les détails du site associé

    class Meta:
        model = Planning
        fields = [
            'id', 'site', 'type', 'jours_passage', 'heure_debut_matin', 'heure_fin_matin',
            'heure_debut_aprem', 'heure_fin_aprem', 'marge_pop_up', 'duree_prevue_minutes'
        ]


class PointageSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Pointage, utilisé pour gérer les données de pointage.
    """
    user = UserSerializer(read_only=True)
    site = SiteSerializer(read_only=True)
    planning = PlanningSerializer(read_only=True)
    date_scan = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = Pointage
        fields = ['id', 'user', 'site', 'planning', 'date_scan', 'arrivee_ou_depart', 'retard', 'depart_anticip', 'periode']

    def to_representation(self, instance):
        logger.debug(f"[TRACKING DATE] PointageSerializer.to_representation - Date entrée: {instance.date_scan} (timezone: {instance.date_scan.tzinfo})")
        
        # Récupérer la représentation par défaut
        data = super().to_representation(instance)
        
        # Préserver la date exacte du scan
        data['date_scan'] = instance.date_scan.strftime("%Y-%m-%dT%H:%M:%S%z")
        logger.debug(f"[TRACKING DATE] Date formatée dans la réponse: {data['date_scan']}")
        
        return data


class AnomalieSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Anomalie, utilisé pour gérer les anomalies signalées.
    """
    user = UserSerializer(read_only=True)  # Inclure les informations de l'utilisateur
    site = SiteSerializer(read_only=True)  # Inclure les informations du site si disponible

    class Meta:
        model = Anomalie
        fields = [
            'id', 'user', 'site', 'motif',
            'date_declaration', 'status'
        ]
