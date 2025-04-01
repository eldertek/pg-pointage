from rest_framework import serializers
from .models import Timesheet, Anomaly, EmployeeReport
from sites.models import Site
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone

class TimesheetSerializer(serializers.ModelSerializer):
    """Serializer pour les pointages"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Timesheet
        fields = [
            'id', 'employee', 'employee_name', 'site', 'site_name',
            'timestamp', 'entry_type', 'latitude', 'longitude',
            'is_late', 'late_minutes', 'is_early_departure',
            'early_departure_minutes', 'correction_note',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        if not obj.employee:
            return ''
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip() or obj.employee.username
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name if obj.site else ''

class TimesheetCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de pointages"""
    site_id = serializers.CharField(write_only=True)
    latitude = serializers.DecimalField(max_digits=12, decimal_places=10, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=12, decimal_places=10, required=False, allow_null=True)
    message = serializers.CharField(read_only=True)
    
    class Meta:
        model = Timesheet
        fields = ['site_id', 'scan_type', 'latitude', 'longitude', 'message']
        extra_kwargs = {
            'scan_type': {'required': True}
        }
    
    def validate_site_id(self, value):
        try:
            return Site.objects.get(nfc_id=value)
        except Site.DoesNotExist:
            raise serializers.ValidationError("Site introuvable avec cet ID NFC/QR Code.")
    
    def validate(self, attrs):
        site = attrs['site_id']
        employee = self.context['request'].user
        today = timezone.now().date()
        
        # Déterminer automatiquement le type d'entrée
        last_timesheet = Timesheet.objects.filter(
            employee=employee,
            site=site,
            timestamp__date=today
        ).order_by('-timestamp').first()
        
        # Si pas de pointage aujourd'hui ou dernier pointage = départ -> arrivée
        # Si dernier pointage = arrivée -> départ
        entry_type = Timesheet.EntryType.ARRIVAL
        message = "Premier pointage de la journée enregistré comme une arrivée."
        
        if last_timesheet:
            if last_timesheet.entry_type == Timesheet.EntryType.ARRIVAL:
                entry_type = Timesheet.EntryType.DEPARTURE
                message = "Pointage enregistré comme un départ suite à votre dernière arrivée."
            else:
                message = "Nouveau cycle de pointage, enregistré comme une arrivée."
        
        attrs['entry_type'] = entry_type
        attrs['message'] = message
        return attrs
    
    def create(self, validated_data):
        site = validated_data.pop('site_id')
        message = validated_data.pop('message')
        employee = self.context['request'].user
        
        # Arrondir les coordonnées GPS à 10 décimales
        if 'latitude' in validated_data:
            validated_data['latitude'] = round(float(validated_data['latitude']), 10)
        if 'longitude' in validated_data:
            validated_data['longitude'] = round(float(validated_data['longitude']), 10)
        
        timesheet = Timesheet.objects.create(
            employee=employee,
            site=site,
            **validated_data
        )
        
        # Ajouter le message à la réponse
        timesheet.message = message
        return timesheet

class AnomalySerializer(serializers.ModelSerializer):
    """Serializer pour les anomalies"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    anomaly_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Anomaly
        fields = ['id', 'employee', 'employee_name', 'site', 'site_name',
                 'anomaly_type', 'anomaly_type_display', 'status', 'status_display',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        return obj.employee.get_full_name() if obj.employee else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name if obj.site else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_anomaly_type_display(self, obj) -> str:
        return obj.get_anomaly_type_display()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

class EmployeeReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports d'employés"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeReport
        fields = '__all__'
        read_only_fields = ['created_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        return obj.employee.get_full_name() or obj.employee.username
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name

