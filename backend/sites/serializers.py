from rest_framework import serializers
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
import logging

class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails de planning"""
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleDetail
        fields = ['id', 'schedule', 'day_of_week', 'day_name', 'start_time_1', 'end_time_1', 
                'start_time_2', 'end_time_2']
    
    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer pour les plannings"""
    details = ScheduleDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'site', 'name', 'schedule_type', 'min_daily_hours', 
                'min_weekly_hours', 'allow_early_arrival', 'allow_late_departure',
                'early_arrival_limit', 'late_departure_limit', 'break_duration',
                'min_break_start', 'max_break_end', 'created_at', 'updated_at', 
                'is_active', 'details']
        read_only_fields = ['created_at', 'updated_at']

class SiteSerializer(serializers.ModelSerializer):
    """Serializer pour les sites"""
    schedules = ScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Site
        fields = ['id', 'name', 'address', 'organization', 'nfc_id', 'qr_code',
                 'late_margin', 'early_departure_margin', 'ambiguous_margin',
                 'alert_emails', 'require_geolocation', 'geolocation_radius',
                 'allow_offline_mode', 'max_offline_duration', 'created_at',
                 'updated_at', 'is_active', 'schedules']
        read_only_fields = ['created_at', 'updated_at']

class SiteEmployeeSerializer(serializers.ModelSerializer):
    """Serializer pour les employés du site"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SiteEmployee
        fields = ['id', 'site', 'employee', 'employee_id', 'employee_name', 'schedule', 'created_at', 'is_active']
        read_only_fields = ['created_at']
        extra_kwargs = {
            'site': {'required': False},
            'employee': {'required': False},
            'schedule': {'required': False}
        }
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
    
    def validate(self, attrs):
        logger = logging.getLogger(__name__)
        logger.info(f"Validation des données: {attrs}")
        
        # Vérifier que employee_id est présent pour la création
        if self.instance is None and 'employee_id' not in attrs:
            logger.error("employee_id manquant lors de la création")
            raise serializers.ValidationError({"employee_id": "Ce champ est obligatoire pour la création."})
        
        return attrs
    
    def create(self, validated_data):
        logger = logging.getLogger(__name__)
        logger.info(f"Création avec les données validées: {validated_data}")
        
        try:
            employee_id = validated_data.pop('employee_id')
            logger.info(f"ID de l'employé extrait: {employee_id}")
            
            instance = SiteEmployee.objects.create(
                employee_id=employee_id,
                **validated_data
            )
            logger.info(f"Instance créée avec succès: {instance}")
            return instance
            
        except Exception as e:
            logger.error(f"Erreur lors de la création: {str(e)}")
            raise

