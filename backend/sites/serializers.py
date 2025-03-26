from rest_framework import serializers
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
import logging
from users.models import User
from .utils import generate_site_id, validate_site_id

class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails de planning"""
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleDetail
        fields = ['id', 'schedule', 'day_of_week', 'day_name', 'start_time_1', 'end_time_1', 
                'start_time_2', 'end_time_2']
    
    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

class SiteEmployeeSerializer(serializers.ModelSerializer):
    """Serializer pour les employés du site"""
    employee_name = serializers.SerializerMethodField()
    employee_organization = serializers.IntegerField(source='employee.organization.id', read_only=True)
    
    class Meta:
        model = SiteEmployee
        fields = ['id', 'site', 'employee', 'employee_name', 'employee_organization', 'schedule', 'created_at', 'is_active']
        read_only_fields = ['created_at', 'employee_name', 'employee_organization']
    
    def get_employee_name(self, obj):
        if isinstance(obj, dict):
            # Si l'objet est un dictionnaire (données non sauvegardées)
            try:
                employee = User.objects.get(id=obj.get('employee'))
                return employee.get_full_name() or employee.username
            except User.DoesNotExist:
                return ''
        # Si l'objet est une instance du modèle
        return obj.employee.get_full_name() or obj.employee.username
    
    def validate(self, attrs):
        logger = logging.getLogger(__name__)
        logger.info(f"Validation des données: {attrs}")
        
        # Vérifier que l'employé appartient à la même organisation que le site
        site = attrs.get('site')
        employee = attrs.get('employee')
        
        if site and employee and site.organization != employee.organization:
            raise serializers.ValidationError("L'employé doit appartenir à la même organisation que le site")
        
        return attrs

class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer pour les plannings"""
    details = ScheduleDetailSerializer(many=True, read_only=True)
    assigned_employees = SiteEmployeeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'site', 'name', 'schedule_type', 'min_daily_hours', 
                'min_weekly_hours', 'allow_early_arrival', 'allow_late_departure',
                'early_arrival_limit', 'late_departure_limit', 'break_duration',
                'min_break_start', 'max_break_end', 'created_at', 'updated_at', 
                'is_active', 'details', 'assigned_employees']
        read_only_fields = ['created_at', 'updated_at']

class SiteSerializer(serializers.ModelSerializer):
    """Serializer pour les sites"""
    schedules = ScheduleSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = ['id', 'name', 'address', 'postal_code', 'city', 'country',
                 'organization', 'organization_name', 'nfc_id', 'qr_code', 'late_margin',
                 'early_departure_margin', 'ambiguous_margin', 'alert_emails',
                 'require_geolocation', 'geolocation_radius', 'allow_offline_mode',
                 'max_offline_duration', 'created_at', 'updated_at', 'is_active',
                 'schedules', 'manager', 'manager_name']
        read_only_fields = ['created_at', 'updated_at', 'organization_name', 'nfc_id']

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name() or obj.manager.username
        return None

    def validate_nfc_id(self, value):
        """Valide le format de l'ID du site"""
        if value and not validate_site_id(value):
            raise serializers.ValidationError(
                'L\'ID du site doit être au format FFF-Sxxxx'
            )
        return value

    def create(self, validated_data):
        """Génère automatiquement l'ID du site"""
        if 'nfc_id' not in validated_data:
            validated_data['nfc_id'] = generate_site_id(validated_data['organization'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Met à jour le site et régénère l'ID si l'organisation change"""
        if 'organization' in validated_data and validated_data['organization'] != instance.organization:
            # Si l'organisation change, générer un nouvel ID
            validated_data['nfc_id'] = generate_site_id(validated_data['organization'])
        return super().update(instance, validated_data)

    def validate(self, attrs):
        # Vérifier que le manager appartient à la même organisation que le site
        manager = attrs.get('manager')
        organization = attrs.get('organization')
        
        if manager and organization and manager.organization != organization:
            raise serializers.ValidationError("Le manager doit appartenir à la même organisation que le site")
        
        return attrs

