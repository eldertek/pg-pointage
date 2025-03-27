from rest_framework import serializers
from .models import Report
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class ReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports"""
    organization_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    report_type_display = serializers.SerializerMethodField()
    report_format_display = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'organization', 'organization_name', 'site', 'site_name',
                 'report_type', 'report_type_display', 'report_format',
                 'report_format_display', 'start_date', 'end_date', 'file',
                 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_at', 'file', 'created_by']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_organization_name(self, obj) -> str:
        return obj.organization.name if obj.organization else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name if obj.site else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_report_type_display(self, obj) -> str:
        return obj.get_report_type_display()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_report_format_display(self, obj) -> str:
        return obj.get_report_format_display()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_created_by_name(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else ''

