from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports"""
    organization_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    report_type_display = serializers.SerializerMethodField()
    report_format_display = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']
    
    def get_organization_name(self, obj):
        return obj.organization.name
    
    def get_site_name(self, obj):
        return obj.site.name if obj.site else None
    
    def get_report_type_display(self, obj):
        return obj.get_report_type_display()
    
    def get_report_format_display(self, obj):
        return obj.get_report_format_display()
    
    def get_creator_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

