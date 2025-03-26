from rest_framework import serializers
from .models import Site, Schedule, ScheduleDetail, SiteEmployee
import logging
from users.models import User
from .utils import generate_site_id, validate_site_id

class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails de planning"""
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleDetail
        fields = [
            'id', 'day_of_week', 'day_type',
            'start_time_1', 'end_time_1',
            'start_time_2', 'end_time_2',
            'frequency_duration'
        ]
    
    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

    def validate(self, data):
        schedule_type = self.context.get('schedule_type')
        if not schedule_type:
            raise serializers.ValidationError("Le type de planning doit être spécifié")
            
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
        
        return data

class SiteEmployeeSerializer(serializers.ModelSerializer):
    """Serializer pour les employés du site"""
    employee_name = serializers.SerializerMethodField()
    employee_organization = serializers.IntegerField(source='employee.organization.id', read_only=True)
    
    class Meta:
        model = SiteEmployee
        fields = ['id', 'site', 'employee', 'employee_name', 'employee_organization', 'schedule', 'created_at', 'is_active']
        read_only_fields = ['created_at', 'employee_name', 'employee_organization']
    
    def get_employee_name(self, obj):
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
            raise serializers.ValidationError("L'employé doit appartenir à la même organisation que le site")
        
        return attrs

class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer pour les plannings"""
    details = ScheduleDetailSerializer(many=True, required=False)
    site_name = serializers.CharField(source='site.name', read_only=True)
    employee = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        queryset=SiteEmployee.objects.all()
    )
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'site', 'site_name', 'schedule_type',
            'details', 'employee', 'created_at', 'updated_at', 'is_active'
        ]
    
    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        employee = validated_data.pop('employee', None)
        
        # Créer le planning
        schedule = Schedule.objects.create(**validated_data)
        
        # Créer les détails du planning
        for detail_data in details_data:
            ScheduleDetail.objects.create(schedule=schedule, **detail_data)
        
        # Assigner l'employé si spécifié
        if employee:
            SiteEmployee.objects.filter(
                site=schedule.site,
                employee=employee.employee
            ).update(schedule=schedule)
        elif SiteEmployee.objects.filter(site=schedule.site).count() == 1:
            # Si un seul employé sur le site, l'assigner automatiquement
            site_employee = SiteEmployee.objects.get(site=schedule.site)
            site_employee.schedule = schedule
            site_employee.save()
        
        return schedule
    
    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', [])
        employee = validated_data.pop('employee', None)
        
        # Mettre à jour le planning
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les détails
        instance.details.all().delete()  # Supprimer les anciens détails
        for detail_data in details_data:
            ScheduleDetail.objects.create(schedule=instance, **detail_data)
        
        # Mettre à jour l'assignation de l'employé
        if employee:
            # Désassigner tous les employés de ce planning
            SiteEmployee.objects.filter(schedule=instance).update(schedule=None)
            # Assigner le nouvel employé
            site_employee = SiteEmployee.objects.get(
                site=instance.site,
                employee=employee.employee
            )
            site_employee.schedule = instance
            site_employee.save()
        
        return instance

class SiteSerializer(serializers.ModelSerializer):
    """Serializer pour les sites"""
    schedules = ScheduleSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = ['id', 'name', 'address', 'postal_code', 'city', 'country',
                 'organization', 'organization_name', 'nfc_id', 'qr_code', 'late_margin',
                 'early_departure_margin', 'ambiguous_margin', 'alert_emails',
                 'require_geolocation', 'geolocation_radius', 'allow_offline_mode',
                 'max_offline_duration', 'created_at', 'updated_at', 'is_active',
                 'schedules', 'manager', 'manager_name']
        read_only_fields = ['created_at', 'updated_at', 'organization_name', 'nfc_id']

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name() or obj.manager.username
        return None

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
            validated_data['nfc_id'] = generate_site_id(validated_data['organization'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Met à jour le site et régénère l'ID si l'organisation change"""
        if 'organization' in validated_data and validated_data['organization'] != instance.organization:
            # Si l'organisation change, générer un nouvel ID
            validated_data['nfc_id'] = generate_site_id(validated_data['organization'])
        return super().update(instance, validated_data)

    def validate(self, attrs):
        # Vérifier que le manager appartient à la même organisation que le site
        manager = attrs.get('manager')
        organization = attrs.get('organization')
        
        if manager and organization and manager.organization != organization:
            raise serializers.ValidationError("Le manager doit appartenir à la même organisation que le site")
        
        return attrs

