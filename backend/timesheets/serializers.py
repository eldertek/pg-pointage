from rest_framework import serializers
from .models import Timesheet, Anomaly, EmployeeReport
from sites.models import Site
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class TimesheetSerializer(serializers.ModelSerializer):
    """Serializer pour les pointages"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Timesheet
        fields = ['id', 'employee', 'employee_name', 'site', 'site_name',
                 'timestamp', 'entry_type', 'created_at']
        read_only_fields = ['created_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        return obj.employee.get_full_name() if obj.employee else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name if obj.site else ''

class TimesheetCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de pointages"""
    site_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = Timesheet
        fields = ['site_id', 'site', 'entry_type', 'timestamp']
    
    def validate_site_id(self, value):
        try:
            site = Site.objects.get(nfc_id=value)
            return site
        except Site.DoesNotExist:
            raise serializers.ValidationError("Site introuvable avec cet ID NFC/QR Code.")
    
    def create(self, validated_data):
        site_id = validated_data.pop('site_id')
        timesheet = Timesheet.objects.create(site=site_id, **validated_data)
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

