from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import (
    User, Site, Planning, Pointage, Anomalie, StatistiquesTemps
)
from django.utils import timezone
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for the Group model (organizations)."""
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    organisation_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'organisation', 'organisation_name', 
            'is_active', 'date_joined'
        ]
        read_only_fields = ['date_joined']
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_organisation_name(self, obj):
        return obj.organisation.name if obj.organisation else None
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class SiteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Site model.
    """
    organisation_name = serializers.SerializerMethodField()
    email_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'qr_code_value', 'emails_alertes', 
            'organisation', 'organisation_name', 'adresse',
            'email_list', 'created_at', 'updated_at'
        ]
    
    def get_organisation_name(self, obj):
        return obj.organisation.name if obj.organisation else None
    
    def get_email_list(self, obj):
        return obj.get_email_list() if hasattr(obj, 'get_email_list') else []


class PlanningSerializer(serializers.ModelSerializer):
    """
    Serializer for the Planning model.
    """
    site_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    jours_passage = serializers.SerializerMethodField()
    
    class Meta:
        model = Planning
        fields = [
            'id', 'site', 'site_name', 'user', 'user_name', 'type',
            'actif', 'date_debut', 'date_fin', 'organisation',
            'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
            'jours_passage', 'heure_debut_matin', 'heure_fin_matin',
            'heure_debut_aprem', 'heure_fin_aprem', 'marge_retard',
            'marge_depart_anticip', 'duree_min', 'frequence', 'marge_duree_pct',
            'created_at', 'updated_at'
        ]
    
    def get_site_name(self, obj):
        return obj.site.name if obj.site else None
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else None
    
    def get_jours_passage(self, obj):
        return obj.get_jours_passage() if hasattr(obj, 'get_jours_passage') else ''


class PointageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Pointage model.
    """
    user_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    planning_info = serializers.SerializerMethodField()
    date_scan = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    
    class Meta:
        model = Pointage
        fields = [
            'id', 'user', 'user_name', 'site', 'site_name', 
            'planning', 'planning_info', 'date_scan', 'periode',
            'type_pointage', 'retard', 'depart_anticip', 'commentaire',
            'organisation', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else None
    
    def get_site_name(self, obj):
        return obj.site.name if obj.site else None
    
    def get_planning_info(self, obj):
        if not obj.planning:
            return None
        return {
            'id': obj.planning.id,
            'type': obj.planning.type,
            'jours_passage': obj.planning.get_jours_passage() if hasattr(obj.planning, 'get_jours_passage') else ''
        }
    
    def to_representation(self, instance):
        logger.debug(f"[TRACKING DATE] PointageSerializer.to_representation - Date entrée: {instance.date_scan} (timezone: {instance.date_scan.tzinfo})")
        
        # Get default representation
        data = super().to_representation(instance)
        
        # Preserve exact scan date
        data['date_scan'] = instance.date_scan.strftime("%Y-%m-%dT%H:%M:%S%z")
        logger.debug(f"[TRACKING DATE] Date formatée dans la réponse: {data['date_scan']}")
        
        return data


class AnomalieSerializer(serializers.ModelSerializer):
    """
    Serializer for the Anomalie model.
    """
    user_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    traite_par_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Anomalie
        fields = [
            'id', 'user', 'user_name', 'site', 'site_name', 
            'date_creation', 'type_anomalie', 'motif', 'status',
            'justificatif', 'date_traitement', 'commentaire_traitement',
            'traite_par', 'traite_par_name', 'minutes_manquantes',
            'organisation', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else None
    
    def get_site_name(self, obj):
        return obj.site.name if obj.site else None
    
    def get_traite_par_name(self, obj):
        return obj.traite_par.username if obj.traite_par else None


class StatistiquesTempsSerializer(serializers.ModelSerializer):
    """
    Serializer for the StatistiquesTemps model.
    """
    user_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    heures_travaillees = serializers.SerializerMethodField()
    heures_retard = serializers.SerializerMethodField()
    heures_depart_anticipe = serializers.SerializerMethodField()
    heures_absence = serializers.SerializerMethodField()
    minutes_manquantes_total = serializers.SerializerMethodField()
    
    class Meta:
        model = StatistiquesTemps
        fields = [
            'id', 'user', 'user_name', 'site', 'site_name',
            'mois', 'annee', 'minutes_travaillees', 'heures_travaillees',
            'minutes_retard', 'heures_retard', 'minutes_depart_anticipe',
            'heures_depart_anticipe', 'minutes_absence', 'heures_absence',
            'jours_travailles', 'minutes_manquantes_total',
            'organisation', 'date_derniere_maj', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else None
    
    def get_site_name(self, obj):
        return obj.site.name if obj.site else None
        
    def get_heures_travaillees(self, obj):
        return obj.heures_travaillees if hasattr(obj, 'heures_travaillees') else None
        
    def get_heures_retard(self, obj):
        return obj.heures_retard if hasattr(obj, 'heures_retard') else None
        
    def get_heures_depart_anticipe(self, obj):
        return obj.heures_depart_anticipe if hasattr(obj, 'heures_depart_anticipe') else None
        
    def get_heures_absence(self, obj):
        return obj.heures_absence if hasattr(obj, 'heures_absence') else None
        
    def get_minutes_manquantes_total(self, obj):
        return obj.minutes_manquantes_total if hasattr(obj, 'minutes_manquantes_total') else None
