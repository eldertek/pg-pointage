from rest_framework import serializers
from .models import Alert
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class AlertSerializer(serializers.ModelSerializer):
    """Serializer pour les alertes"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    alert_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = ['id', 'employee', 'employee_name', 'site', 'site_name',
                 'alert_type', 'alert_type_display', 'status', 'status_display',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        return obj.employee.get_full_name() if obj.employee else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name if obj.site else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_alert_type_display(self, obj) -> str:
        return obj.get_alert_type_display()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

