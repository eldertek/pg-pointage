""" Serializers pour les sites, les plannings et les employés """
from rest_framework import serializers
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
import logging
from users.models import User
from .utils import generate_site_id, validate_site_id
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails de planning"""
    day_name = serializers.SerializerMethodField()
    schedule_type = serializers.CharField(write_only=True)

    class Meta:
        model = ScheduleDetail
        fields = [
            'id', 'day_of_week', 'day_type',
            'start_time_1', 'end_time_1',
            'start_time_2', 'end_time_2',
            'frequency_duration', 'day_name',
            'schedule_type'
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_day_name(self, obj) -> str:
        return obj.get_day_of_week_display()

    def validate(self, data):
        schedule_type = data.get('schedule_type')
        if not schedule_type:
            raise serializers.ValidationError(
                "Le type de planning doit être spécifié")

        if schedule_type == Schedule.ScheduleType.FIXED:
            # Validation pour planning fixe
            if 'frequency_duration' in data:
                raise serializers.ValidationError({
                    'frequency_duration': 'La durée ne doit pas être définie pour un planning fixe'
                })

            day_type = data.get('day_type')
            if day_type == ScheduleDetail.DayType.FULL:
                if not all([data.get('start_time_1'), data.get('end_time_1'),
                            data.get('start_time_2'), data.get('end_time_2')]):
                    raise serializers.ValidationError(
                        'Tous les horaires doivent être définis pour une journée entière'
                    )
            elif day_type == ScheduleDetail.DayType.AM:
                if not all([data.get('start_time_1'), data.get('end_time_1')]):
                    raise serializers.ValidationError(
                        'Les horaires du matin doivent être définis'
                    )
                if any([data.get('start_time_2'), data.get('end_time_2')]):
                    raise serializers.ValidationError(
                        'Les horaires de l\'après-midi ne doivent pas être définis'
                    )
            else:  # PM
                if not all([data.get('start_time_2'), data.get('end_time_2')]):
                    raise serializers.ValidationError(
                        'Les horaires de l\'après-midi doivent être définis'
                    )
                if any([data.get('start_time_1'), data.get('end_time_1')]):
                    raise serializers.ValidationError(
                        'Les horaires du matin ne doivent pas être définis'
                    )
        else:
            # Validation pour planning fréquence
            if not data.get('frequency_duration'):
                raise serializers.ValidationError({
                    'frequency_duration': 'La durée doit être définie pour un planning fréquence'
                })
            if any([data.get('start_time_1'), data.get('end_time_1'),
                   data.get('start_time_2'), data.get('end_time_2')]):
                raise serializers.ValidationError(
                    'Les horaires ne doivent pas être définis pour un planning fréquence'
                )

            # Validation de la durée en minutes
            frequency_duration = data.get('frequency_duration')
            if frequency_duration is not None:
                if frequency_duration < 0:
                    raise serializers.ValidationError({
                        'frequency_duration': 'La durée ne peut pas être négative'
                    })
                if frequency_duration > 1440:  # 24h * 60min
                    raise serializers.ValidationError({
                        'frequency_duration': 'La durée ne peut pas dépasser 24 heures (1440 minutes)'
                    })

        # Supprimer le schedule_type des données avant la création
        data.pop('schedule_type', None)
        return data


class SiteEmployeeSerializer(serializers.ModelSerializer):
    """Serializer pour les employés du site"""
    employee_name = serializers.SerializerMethodField()
    employee_organization = serializers.IntegerField(
        source='employee.organization.id', read_only=True)

    class Meta:
        model = SiteEmployee
        fields = ['id', 'site', 'employee', 'employee_name',
                  'employee_organization', 'schedule', 'created_at', 'is_active']
        read_only_fields = ['created_at',
                            'employee_name', 'employee_organization']

    @extend_schema_field(OpenApiTypes.STR)
    def get_employee_name(self, obj) -> str:
        if isinstance(obj, dict):
            # Si l'objet est un dictionnaire (données non sauvegardées)
            try:
                employee = User.objects.get(id=obj.get('employee'))
                return employee.get_full_name() or employee.username
            except User.DoesNotExist:
                return ''
        # Si l'objet est une instance du modèle
        return obj.employee.get_full_name() or obj.employee.username

    def validate(self, attrs):
        logger = logging.getLogger(__name__)
        logger.info(f"Validation des données: {attrs}")

        # Vérifier que l'employé appartient à la même organisation que le site
        site = attrs.get('site')
        employee = attrs.get('employee')

        if site and employee and site.organization != employee.organization:
            raise serializers.ValidationError(
                "L'employé doit appartenir à la même organisation que le site")

        return attrs


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer pour les plannings"""
    details = ScheduleDetailSerializer(many=True, required=False)
    site_name = serializers.CharField(source='site.name', read_only=True)
    employees = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    assigned_employees = serializers.SerializerMethodField()
    assigned_employee_ids = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            'id', 'site', 'site_name', 'schedule_type',
            'details', 'employees', 'created_at', 'updated_at', 'is_active',
            'assigned_employees', 'assigned_employee_ids',
            'frequency_tolerance_percentage',
            'late_arrival_margin', 'early_departure_margin'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Validation personnalisée des données"""
        schedule_type = data.get('schedule_type')
        details = data.get('details', [])

        # Validation des marges selon le type de planning
        if schedule_type == Schedule.ScheduleType.FIXED:
            # Validation des marges pour les plannings fixes
            if data.get('frequency_tolerance_percentage') is not None:
                raise serializers.ValidationError({
                    'frequency_tolerance_percentage': 'La marge de tolérance en pourcentage ne doit pas être définie pour un planning fixe'
                })

            # Vérifier que les marges sont définies pour les plannings fixes
            if data.get('late_arrival_margin') is None:
                data['late_arrival_margin'] = 0
            if data.get('early_departure_margin') is None:
                data['early_departure_margin'] = 0

            # Validation des valeurs des marges
            if data['late_arrival_margin'] < 0:
                raise serializers.ValidationError({
                    'late_arrival_margin': 'La marge de retard ne peut pas être négative'
                })
            if data['early_departure_margin'] < 0:
                raise serializers.ValidationError({
                    'early_departure_margin': 'La marge de départ anticipé ne peut pas être négative'
                })
        else:
            # Validation des marges pour les plannings fréquence
            if any([
                data.get('late_arrival_margin') is not None,
                data.get('early_departure_margin') is not None
            ]):
                raise serializers.ValidationError(
                    'Les marges en minutes ne doivent pas être définies pour un planning fréquence'
                )

            # Vérifier que la marge de tolérance est définie pour les plannings fréquence
            if data.get('frequency_tolerance_percentage') is None:
                data['frequency_tolerance_percentage'] = 10  # Valeur par défaut

            # Validation de la valeur de la marge
            if not (0 <= data['frequency_tolerance_percentage'] <= 100):
                raise serializers.ValidationError({
                    'frequency_tolerance_percentage': 'La marge de tolérance doit être comprise entre 0 et 100%'
                })

        # Validation des détails du planning
        if details:
            # Ajouter le type de planning à chaque détail
            for detail in details:
                detail['schedule_type'] = schedule_type

            detail_serializer = ScheduleDetailSerializer(
                data=details, many=True)
            detail_serializer.is_valid(raise_exception=True)
            data['details'] = detail_serializer.validated_data

        return data

    def get_assigned_employee_ids(self, obj):
        """Retourne la liste des IDs des employés assignés au planning"""
        return [
            se.employee.id
            for se in SiteEmployee.objects.filter(
                site=obj.site,
                schedule=obj,
                is_active=True
            ).select_related('employee')
        ]

    def get_assigned_employees(self, obj):
        employees = SiteEmployee.objects.filter(
            site=obj.site,
            schedule=obj,
            is_active=True
        ).select_related('employee')
        return SiteEmployeeSerializer(employees, many=True).data

    def create(self, validated_data):
        print("[ScheduleSerializer][Debug] Début de la création d'un planning")
        details_data = validated_data.pop('details', [])
        employees_data = validated_data.pop('employees', [])

        # Créer le planning
        schedule = Schedule.objects.create(**validated_data)
        print(
            f"[ScheduleSerializer][Debug] Planning créé avec l'ID: {schedule.id}")

        # Créer les détails du planning
        for detail_data in details_data:
            # Retirer schedule_type des données avant création
            detail_data.pop('schedule_type', None)
            ScheduleDetail.objects.create(
                schedule=schedule,
                **detail_data
            )

        # Assigner les employés au planning
        if employees_data:
            print(
                f"[ScheduleSerializer][Debug] Assignation des employés: {employees_data}")
            for employee_id in employees_data:
                site_employee, created = create_or_update_site_employee(
                    site=schedule.site,
                    employee_id=employee_id,
                    schedule=schedule
                )
                if site_employee:
                    print(
                        f"[ScheduleSerializer][Debug] Employé {employee_id} {'ajouté au' if created else 'mis à jour dans le'} planning {schedule.id}")
                else:
                    print(
                        f"[ScheduleSerializer][Warning] Erreur lors de l'assignation de l'employé {employee_id}")

        return schedule

    def update(self, instance, validated_data):
        print(
            f"[ScheduleSerializer][Debug] Mise à jour du planning {instance.id}")
        details_data = validated_data.pop('details', [])
        employees_data = validated_data.pop('employees', None)

        # Mettre à jour les champs du planning
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Mettre à jour les détails si fournis
        if details_data is not None:
            # Supprimer les anciens détails
            instance.details.all().delete()

            # Créer les nouveaux détails
            for detail_data in details_data:
                # Retirer schedule_type des données avant création
                detail_data.pop('schedule_type', None)
                ScheduleDetail.objects.create(
                    schedule=instance,
                    **detail_data
                )

        # Mettre à jour les employés si fournis
        if employees_data is not None:
            print(
                f"[ScheduleSerializer][Debug] Mise à jour des employés: {employees_data}")

            # Désactiver les relations SiteEmployee pour ce planning qui ne sont plus dans la liste
            SiteEmployee.objects.filter(
                site=instance.site,
                schedule=instance
            ).exclude(
                employee_id__in=employees_data
            ).update(schedule=None)

            # Assigner ou mettre à jour les employés fournis
            for employee_id in employees_data:
                site_employee, created = create_or_update_site_employee(
                    site=instance.site,
                    employee_id=employee_id,
                    schedule=instance
                )
                if site_employee:
                    print(
                        f"[ScheduleSerializer][Debug] Employé {employee_id} {'ajouté au' if created else 'mis à jour dans le'} planning {instance.id}")
                else:
                    print(
                        f"[ScheduleSerializer][Warning] Erreur lors de l'assignation de l'employé {employee_id}")

        return instance

    def to_internal_value(self, data):
        # Si le site est envoyé comme un dictionnaire avec un id, extraire l'id
        if isinstance(data.get('site'), dict) and 'id' in data['site']:
            data['site'] = data['site']['id']
        return super().to_internal_value(data)


class SiteSerializer(serializers.ModelSerializer):
    """Serializer pour les sites"""
    schedules = ScheduleSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(
        source='organization.name', read_only=True)
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ['id', 'name', 'address', 'postal_code', 'city', 'country',
                  'organization', 'organization_name', 'manager', 'manager_name', 'nfc_id', 'qr_code', 'late_margin',
                  'early_departure_margin', 'ambiguous_margin', 'alert_emails',
                  'require_geolocation', 'geolocation_radius', 'allow_offline_mode',
                  'max_offline_duration', 'created_at', 'updated_at', 'is_active',
                  'schedules']
        read_only_fields = ['created_at', 'updated_at',
                            'organization_name', 'nfc_id']
        extra_kwargs = {
            'name': {'required': True, 'error_messages': {'required': 'Ce champ est obligatoire.'}},
            'address': {'required': True, 'error_messages': {'required': 'Ce champ est obligatoire.'}},
            'postal_code': {'required': True, 'error_messages': {'required': 'Ce champ est obligatoire.'}},
            'city': {'required': True, 'error_messages': {'required': 'Ce champ est obligatoire.'}},
            'organization': {'required': True, 'error_messages': {'required': 'Ce champ est obligatoire.'}},
            'manager': {'required': False},
            'country': {'required': False, 'default': 'France'},
            'late_margin': {'required': False, 'default': 15},
            'early_departure_margin': {'required': False, 'default': 15},
            'ambiguous_margin': {'required': False, 'default': 20},
            'require_geolocation': {'required': False, 'default': True},
            'geolocation_radius': {'required': False, 'default': 100},
            'allow_offline_mode': {'required': False, 'default': True},
            'max_offline_duration': {'required': False, 'default': 24},
            'is_active': {'required': False, 'default': True}
        }

    @extend_schema_field(OpenApiTypes.STR)
    def get_manager_name(self, obj):
        """Retourne le nom complet du manager"""
        if obj.manager:
            return obj.manager.get_full_name() or obj.manager.username
        return None

    def validate(self, attrs):
        """Validation personnalisée pour le manager et l'organisation"""
        manager = attrs.get('manager')
        organization = attrs.get('organization')

        if manager:
            # Vérifier que le manager existe et a le bon rôle
            if manager.role != 'MANAGER':
                raise serializers.ValidationError({
                    'manager': 'L\'utilisateur sélectionné doit avoir le rôle de manager'
                })

            # Si l'organisation est fournie, vérifier que le manager y appartient
            if organization and not manager.organizations.filter(id=organization.id).exists():
                raise serializers.ValidationError({
                    'manager': 'Le manager doit appartenir à l\'organisation du site'
                })

            # Si l'organisation n'est pas fournie mais qu'on est en update,
            # vérifier avec l'organisation existante
            elif not organization and self.instance:
                if not manager.organizations.filter(id=self.instance.organization.id).exists():
                    raise serializers.ValidationError({
                        'manager': 'Le manager doit appartenir à l\'organisation du site'
                    })

        return attrs

    def validate_nfc_id(self, value):
        """Valide le format de l'ID du site"""
        if value and not validate_site_id(value):
            raise serializers.ValidationError(
                'L\'ID du site doit être au format FFF-Sxxxx'
            )
        return value

    def create(self, validated_data):
        """Génère automatiquement l'ID du site"""
        if 'nfc_id' not in validated_data:
            validated_data['nfc_id'] = generate_site_id(
                validated_data['organization'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Met à jour le site et régénère l'ID si l'organisation change"""
        if 'organization' in validated_data and validated_data['organization'] != instance.organization:
            # Si l'organisation change, générer un nouvel ID
            validated_data['nfc_id'] = generate_site_id(
                validated_data['organization'])
        return super().update(instance, validated_data)


class SiteStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'un site"""
    total_employees = serializers.IntegerField()
    total_hours = serializers.IntegerField()
    anomalies = serializers.IntegerField()


def create_or_update_site_employee(site, employee_id, schedule):
    """
    Crée ou met à jour une relation SiteEmployee
    """
    try:
        # Vérifier d'abord si la relation existe déjà avec ce planning spécifique
        site_employee = SiteEmployee.objects.filter(
            site=site,
            employee_id=employee_id,
            schedule=schedule
        ).first()

        if site_employee:
            # Si elle existe, on s'assure qu'elle est active
            site_employee.is_active = True
            site_employee.save()
            return site_employee, False

        # Si elle n'existe pas avec ce planning, on la crée
        site_employee = SiteEmployee.objects.create(
            site=site,
            employee_id=employee_id,
            schedule=schedule,
            is_active=True
        )
        return site_employee, True
    except Exception as e:
        print(f"[create_or_update_site_employee][Error] {str(e)}")
        return None, False
