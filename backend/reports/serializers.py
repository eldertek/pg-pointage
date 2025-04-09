from rest_framework import serializers
from .models import Report
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from core.mixins import OrganizationPermissionMixin, RolePermissionMixin, SitePermissionMixin
from users.models import User

class ReportSerializer(serializers.ModelSerializer, OrganizationPermissionMixin, RolePermissionMixin, SitePermissionMixin):
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
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Vérifier que l'utilisateur a le droit de générer des rapports
        if user.role == User.Role.EMPLOYEE:
            raise serializers.ValidationError("Les employés ne peuvent pas générer de rapports")
        
        # Vérifier l'accès à l'organisation
        if 'organization' in data:
            self.validate_organization(data['organization'].id)
        
        # Vérifier l'accès au site
        if 'site' in data:
            self.validate_site(data['site'])
            
            # Vérifier que le site appartient à l'organisation
            if data['site'].organization != data['organization']:
                raise serializers.ValidationError({
                    "site": "Le site n'appartient pas à l'organisation sélectionnée"
                })
        
        # Validation des dates
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError({
                'end_date': 'La date de fin doit être postérieure à la date de début'
            })
        
        return data
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_organization_name(self, obj) -> str:
        return obj.organization.name if obj.organization else ''
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_created_by_name(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else ''

    def get_period(self, obj):
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"

class ReportGenerateSerializer(serializers.Serializer, OrganizationPermissionMixin, SitePermissionMixin):
    """Serializer pour la génération de rapports"""
    name = serializers.CharField(max_length=255)
    report_type = serializers.ChoiceField(choices=Report.ReportType.choices)
    report_format = serializers.ChoiceField(choices=Report.ReportFormat.choices)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    site = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        print(f"[Reports][Validate] Début de la validation - Données: {data}")
        user = self.context['request'].user
        
        # Vérifier que l'utilisateur a le droit de générer des rapports
        if user.role == User.Role.EMPLOYEE:
            print("[Reports][Validate] Erreur: L'utilisateur est un employé")
            raise serializers.ValidationError("Les employés ne peuvent pas générer de rapports")
        
        # Validation des dates
        if data['end_date'] < data['start_date']:
            print("[Reports][Validate] Erreur: La date de fin est antérieure à la date de début")
            raise serializers.ValidationError({
                'end_date': 'La date de fin doit être postérieure à la date de début'
            })

        # Validation du site si spécifié
        site = data.get('site')
        print(f"[Reports][Validate] Site reçu: {site} (type: {type(site)})")
        
        # Si site n'est pas dans les données, ou est None, 0, ou chaîne vide - traiter comme null
        if site in [None, '', 0, '0']:
            print("[Reports][Validate] Site null détecté - Rapport pour tous les sites")
            # Aucune validation nécessaire, rapport pour tous les sites
            data['site'] = None  # Normaliser à None
        else:
            print(f"[Reports][Validate] Validation du site spécifié: {site}")
            from sites.models import Site
            try:
                site_obj = Site.objects.get(id=site)
                if not user.is_super_admin:
                    print("[Reports][Validate] Vérification des permissions sur le site")
                    self.validate_site(site_obj)
                print(f"[Reports][Validate] Site validé: {site_obj.name}")
            except Site.DoesNotExist:
                print(f"[Reports][Validate] Erreur: Le site {site} n'existe pas")
                raise serializers.ValidationError({
                    'site': 'Le site spécifié n\'existe pas'
                })

        print("[Reports][Validate] Validation terminée avec succès")
        return data

