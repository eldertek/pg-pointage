from rest_framework import serializers
from .models import Report
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class ReportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports"""
    organization_name = serializers.SerializerMethodField()
    site_name = serializers.CharField(source='site.name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    report_format_display = serializers.CharField(source='get_report_format_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'organization', 'organization_name', 'site', 'site_name',
            'report_type', 'report_type_display', 'report_format',
            'report_format_display', 'start_date', 'end_date', 'file',
            'created_by', 'created_by_name', 'created_at', 'period'
        ]
        read_only_fields = ['created_at', 'file', 'created_by']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_organization_name(self, obj) -> str:
        return obj.organization.name if obj.organization else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_created_by_name(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else ''

    def get_period(self, obj):
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"

class ReportGenerateSerializer(serializers.Serializer):
    """Serializer pour la génération de rapports"""
    name = serializers.CharField(max_length=255)
    report_type = serializers.ChoiceField(choices=Report.ReportType.choices)
    report_format = serializers.ChoiceField(choices=Report.ReportFormat.choices)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    site = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        """Validation des dates et autres champs"""
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError({
                'end_date': 'La date de fin doit être postérieure à la date de début'
            })

        # Validation du site si fourni
        site = data.get('site')
        if site is not None:
            from sites.models import Site
            if not Site.objects.filter(id=site).exists():
                raise serializers.ValidationError({
                    'site': 'Site invalide'
                })

        return data

