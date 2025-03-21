from rest_framework import serializers
from .models import Timesheet, Anomaly, EmployeeReport
from sites.models import Site

class TimesheetSerializer(serializers.ModelSerializer):
    """Serializer pour les pointages"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Timesheet
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
    
    def get_site_name(self, obj):
        return obj.site.name

class TimesheetCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de pointages"""
    site_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = Timesheet
        fields = ['site_id', 'timestamp', 'entry_type', 'latitude', 'longitude']
    
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
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'corrected_by', 'correction_date']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
    
    def get_site_name(self, obj):
        return obj.site.name
    
    def get_anomaly_type_display(self, obj):
        return obj.get_anomaly_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()

class EmployeeReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports d'employés"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeReport
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
    
    def get_site_name(self, obj):
        return obj.site.name

