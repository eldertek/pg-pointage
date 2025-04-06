from rest_framework import serializers
from .models import Timesheet, Anomaly, EmployeeReport
from sites.models import Site
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from core.mixins import OrganizationPermissionMixin, RolePermissionMixin, SitePermissionMixin
from users.models import User

class TimesheetSerializer(serializers.ModelSerializer, OrganizationPermissionMixin, SitePermissionMixin):
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

    def validate(self, data):
        user = self.context['request'].user

        # Vérifier l'accès au site
        if 'site' in data:
            self.validate_site(data['site'])

        # Seuls les managers et admins peuvent modifier les pointages d'autres employés
        if 'employee' in data and data['employee'].id != user.id:
            if not (user.is_super_admin or user.is_admin or user.is_manager):
                raise serializers.ValidationError({
                    "employee": "Vous ne pouvez pas modifier les pointages d'autres employés"
                })

            # Les managers ne peuvent modifier que les pointages des employés de leurs sites
            if user.is_manager:
                if not user.organizations.filter(sites__employees=data['employee']).exists():
                    raise serializers.ValidationError({
                        "employee": "Vous ne pouvez pas modifier les pointages de cet employé"
                    })

        return data

    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        if not obj.employee:
            return ''
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip() or obj.employee.username

    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name if obj.site else ''

class TimesheetCreateSerializer(serializers.ModelSerializer, SitePermissionMixin):
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
            site = Site.objects.get(nfc_id=value)
            # Vérifier que l'utilisateur a accès à ce site
            self.validate_site(site)
            return site
        except Site.DoesNotExist:
            raise serializers.ValidationError("Site introuvable avec cet ID NFC/QR Code.")

    def validate(self, attrs):
        site = attrs['site_id']
        employee = self.context['request'].user
        today = timezone.now().date()

        # Vérifier que l'employé est actif
        if not employee.is_active:
            raise serializers.ValidationError("Votre compte est inactif.")

        # Vérifier que l'employé est rattaché au site
        if not employee.organizations.filter(sites=site).exists():
            raise serializers.ValidationError("Vous n'êtes pas autorisé à pointer sur ce site.")

        # Déterminer automatiquement le type d'entrée
        last_timesheet = Timesheet.objects.filter(
            employee=employee,
            site=site,
            timestamp__date=today
        ).order_by('-timestamp').first()

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
        # Extraire le message avant de créer l'objet Timesheet
        message = validated_data.pop('message', '')

        # Ajouter l'employé (l'utilisateur connecté) aux données validées
        validated_data['employee'] = self.context['request'].user

        # Récupérer l'objet site à partir de site_id et le remplacer dans validated_data
        site = validated_data.pop('site_id')
        validated_data['site'] = site

        # Créer l'objet Timesheet sans le champ message
        timesheet = Timesheet.objects.create(**validated_data)

        # Stocker le message pour qu'il soit disponible dans la réponse
        self._message = message

        return timesheet

    def to_representation(self, instance):
        # Ajouter le message à la représentation de l'objet
        ret = super().to_representation(instance)
        ret['message'] = getattr(self, '_message', '')
        return ret

class AnomalySerializer(serializers.ModelSerializer, OrganizationPermissionMixin, SitePermissionMixin):
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

    def validate(self, data):
        user = self.context['request'].user

        # Vérifier l'accès au site
        if 'site' in data:
            self.validate_site(data['site'])

        # Seuls les managers et admins peuvent modifier le statut des anomalies
        if 'status' in data and not (user.is_super_admin or user.is_admin or user.is_manager):
            raise serializers.ValidationError({
                "status": "Vous n'avez pas les droits pour modifier le statut d'une anomalie"
            })

        # Les managers ne peuvent gérer que les anomalies de leurs sites
        if user.is_manager:
            if 'site' in data and not user.organizations.filter(sites=data['site']).exists():
                raise serializers.ValidationError({
                    "site": "Vous ne pouvez pas gérer les anomalies de ce site"
                })

        return data

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

class EmployeeReportSerializer(serializers.ModelSerializer, OrganizationPermissionMixin, SitePermissionMixin):
    """Serializer pour les rapports d'employés"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeReport
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate(self, data):
        user = self.context['request'].user

        # Vérifier l'accès au site
        if 'site' in data:
            self.validate_site(data['site'])

        # Seuls les managers et admins peuvent créer/modifier des rapports
        if not (user.is_super_admin or user.is_admin or user.is_manager):
            raise serializers.ValidationError("Vous n'avez pas les droits pour gérer les rapports d'employés")

        # Les managers ne peuvent gérer que les rapports de leurs sites
        if user.is_manager:
            if 'site' in data and not user.organizations.filter(sites=data['site']).exists():
                raise serializers.ValidationError({
                    "site": "Vous ne pouvez pas gérer les rapports de ce site"
                })

        return data

    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        return obj.employee.get_full_name() or obj.employee.username

    @extend_schema_field(OpenApiTypes.STR)
    def get_site_name(self, obj) -> str:
        return obj.site.name

