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
    schedule_details = serializers.SerializerMethodField()

    class Meta:
        model = Timesheet
        fields = [
            'id', 'employee', 'employee_name', 'site', 'site_name',
            'timestamp', 'entry_type', 'latitude', 'longitude',
            'is_late', 'late_minutes', 'is_early_departure',
            'early_departure_minutes', 'correction_note',
            'created_at', 'updated_at', 'schedule_details'
        ]
        read_only_fields = ['created_at', 'updated_at', 'schedule_details']
        extra_kwargs = {
            'employee': {'required': False},
            'site': {'required': False}
        }

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

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_schedule_details(self, obj):
        """Récupère les détails du planning associé au pointage"""
        # Récupérer le planning associé au pointage
        from sites.models import SiteEmployee, Schedule, ScheduleDetail

        # Récupérer la date du pointage
        timestamp_date = obj.timestamp.date()
        day_of_week = obj.timestamp.weekday()

        # Récupérer les relations site-employé pour cet employé et ce site
        site_employee_relations = SiteEmployee.objects.filter(
            site=obj.site,
            employee=obj.employee,
            is_active=True
        ).select_related('schedule')

        # Chercher le planning correspondant
        for site_employee in site_employee_relations:
            schedule = site_employee.schedule
            if not schedule or not schedule.is_active:
                continue

            # Vérifier si le planning a des détails pour ce jour
            try:
                schedule_detail = ScheduleDetail.objects.get(
                    schedule=schedule,
                    day_of_week=day_of_week
                )

                # Vérifier si le pointage correspond à ce planning
                if schedule.schedule_type == 'FIXED':
                    # Pour les plannings fixes, vérifier si l'heure du pointage est dans les plages horaires
                    timesheet_time = obj.timestamp.time()

                    # Plage du matin
                    if schedule_detail.start_time_1 and schedule_detail.end_time_1:
                        if schedule_detail.start_time_1 <= timesheet_time <= schedule_detail.end_time_1:
                            return self._format_schedule_details(schedule, schedule_detail)

                    # Plage de l'après-midi
                    if schedule_detail.start_time_2 and schedule_detail.end_time_2:
                        if schedule_detail.start_time_2 <= timesheet_time <= schedule_detail.end_time_2:
                            return self._format_schedule_details(schedule, schedule_detail)

                elif schedule.schedule_type == 'FREQUENCY':
                    # Pour les plannings fréquence, tous les pointages du jour sont valides
                    return self._format_schedule_details(schedule, schedule_detail)

            except ScheduleDetail.DoesNotExist:
                continue

        return None

    def _format_schedule_details(self, schedule, schedule_detail):
        """Formate les détails du planning pour la réponse"""
        result = {
            'id': schedule.id,
            'name': f"Planning {schedule.id} - {schedule.site.name}",
            'schedule_type': schedule.schedule_type,
            'schedule_type_display': schedule.get_schedule_type_display(),
            'is_active': schedule.is_active
        }

        # Ajouter les détails spécifiques au jour
        if schedule.schedule_type == 'FIXED':
            result.update({
                'start_time_1': schedule_detail.start_time_1,
                'end_time_1': schedule_detail.end_time_1,
                'start_time_2': schedule_detail.start_time_2,
                'end_time_2': schedule_detail.end_time_2
            })
        elif schedule.schedule_type == 'FREQUENCY':
            result.update({
                'frequency_duration': schedule_detail.frequency_duration,
                'tolerance_percentage': schedule.frequency_tolerance_percentage
            })

        return result

class TimesheetCreateSerializer(serializers.ModelSerializer, SitePermissionMixin):
    """Serializer pour la création de pointages"""
    site_id = serializers.CharField(write_only=True)
    latitude = serializers.DecimalField(max_digits=12, decimal_places=10, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=12, decimal_places=10, required=False, allow_null=True)
    message = serializers.CharField(read_only=True)
    entry_type = serializers.CharField(required=False, write_only=True)
    timestamp = serializers.DateTimeField(required=False, write_only=True)

    class Meta:
        model = Timesheet
        fields = ['site_id', 'scan_type', 'latitude', 'longitude', 'message', 'entry_type', 'timestamp']
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

        # Utiliser le timestamp fourni ou générer un nouveau
        if 'timestamp' in attrs:
            timestamp = attrs['timestamp']
            # S'assurer que le timestamp est un objet datetime
            if isinstance(timestamp, str):
                timestamp = timezone.parse_datetime(timestamp)
                attrs['timestamp'] = timestamp
            today = timestamp.date()
        else:
            attrs['timestamp'] = timezone.now()

        # Vérifier que l'employé est actif
        if not employee.is_active:
            raise serializers.ValidationError("Votre compte est inactif.")

        # Vérifier que l'employé est rattaché au site
        if not employee.organizations.filter(sites=site).exists():
            raise serializers.ValidationError("Vous n'êtes pas autorisé à pointer sur ce site.")

        # Si le type d'entrée est spécifié (cas ambigu), l'utiliser
        if 'entry_type' in attrs and attrs['entry_type']:
            entry_type = attrs['entry_type']
            if entry_type == Timesheet.EntryType.ARRIVAL:
                message = "Pointage enregistré comme une arrivée (cas ambigu)."
            else:
                message = "Pointage enregistré comme un départ (cas ambigu)."
        else:
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

        # Vérifier s'il existe déjà un pointage avec le même timestamp (pour éviter les doublons)
        existing_timesheet = Timesheet.objects.filter(
            employee=employee,
            site=site,
            timestamp=attrs['timestamp']
        ).first()

        if existing_timesheet:
            # Si un pointage existe déjà à ce moment précis, ajouter une seconde pour éviter le doublon
            attrs['timestamp'] = attrs['timestamp'] + timezone.timedelta(seconds=1)

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
    timesheet_details = serializers.SerializerMethodField()
    schedule_details = serializers.SerializerMethodField()
    related_timesheets_details = serializers.SerializerMethodField()
    translated_description = serializers.SerializerMethodField()

    class Meta:
        model = Anomaly
        fields = ['id', 'employee', 'employee_name', 'site', 'site_name',
                 'anomaly_type', 'anomaly_type_display', 'status', 'status_display',
                 'description', 'translated_description', 'date', 'minutes', 'timesheet', 'timesheet_details',
                 'schedule', 'schedule_details', 'related_timesheets_details',
                 'created_at', 'updated_at', 'corrected_by']
        read_only_fields = ['created_at', 'updated_at', 'description', 'translated_description', 'date', 'minutes',
                           'timesheet_details', 'schedule_details', 'related_timesheets_details']

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

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_timesheet_details(self, obj):
        """Récupère les détails du pointage associé à l'anomalie"""
        if not obj.timesheet:
            return None

        timesheet = obj.timesheet
        return {
            'id': timesheet.id,
            'timestamp': timesheet.timestamp,
            'entry_type': timesheet.entry_type,
            'entry_type_display': timesheet.get_entry_type_display(),
            'is_late': timesheet.is_late,
            'late_minutes': timesheet.late_minutes,
            'is_early_departure': timesheet.is_early_departure,
            'early_departure_minutes': timesheet.early_departure_minutes,
            'is_out_of_schedule': timesheet.is_out_of_schedule
        }

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_schedule_details(self, obj):
        """Récupère les détails du planning associé à l'anomalie"""
        if not obj.schedule:
            return None

        schedule = obj.schedule
        from sites.models import ScheduleDetail

        # Récupérer les détails du planning pour le jour de l'anomalie
        schedule_detail = None
        try:
            if obj.date:
                schedule_detail = ScheduleDetail.objects.filter(
                    schedule=schedule,
                    day_of_week=obj.date.weekday()
                ).first()
        except Exception as e:
            # En cas d'erreur, on continue sans les détails
            pass

        result = {
            'id': schedule.id,
            'name': f"Planning {schedule.id} - {schedule.site.name}",
            'schedule_type': schedule.schedule_type,
            'schedule_type_display': schedule.get_schedule_type_display(),
            'is_active': schedule.is_active
        }

        # Ajouter les détails spécifiques au jour si disponibles
        if schedule_detail:
            if schedule.schedule_type == 'FIXED':
                result.update({
                    'start_time_1': schedule_detail.start_time_1,
                    'end_time_1': schedule_detail.end_time_1,
                    'start_time_2': schedule_detail.start_time_2,
                    'end_time_2': schedule_detail.end_time_2
                })
            elif schedule.schedule_type == 'FREQUENCY':
                result.update({
                    'frequency_duration': schedule_detail.frequency_duration,
                    'tolerance_percentage': schedule.frequency_tolerance_percentage
                })

        return result

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_related_timesheets_details(self, obj):
        """Récupère les détails des pointages associés à l'anomalie"""
        related_timesheets = obj.related_timesheets.all()
        if not related_timesheets:
            return []

        result = []
        for timesheet in related_timesheets:
            result.append({
                'id': timesheet.id,
                'timestamp': timesheet.timestamp,
                'entry_type': timesheet.entry_type,
                'entry_type_display': timesheet.get_entry_type_display(),
                'is_late': timesheet.is_late,
                'late_minutes': timesheet.late_minutes,
                'is_early_departure': timesheet.is_early_departure,
                'early_departure_minutes': timesheet.early_departure_minutes,
                'is_out_of_schedule': timesheet.is_out_of_schedule
            })

        return result

    @extend_schema_field(OpenApiTypes.STR)
    def get_translated_description(self, obj):
        """Récupère la description traduite de l'anomalie en fonction de la langue de l'utilisateur"""
        from django.utils.translation import gettext as _
        import re

        # Récupérer la langue de l'utilisateur depuis la requête
        request = self.context.get('request')
        if not request or not obj.description:
            return obj.description

        # Traduire les descriptions en fonction du type d'anomalie
        if obj.anomaly_type == Anomaly.AnomalyType.LATE:
            if 'Retard de' in obj.description:
                # Extraire les informations numériques
                minutes_match = re.search(r'Retard de (\d+) minute\(s\)', obj.description)
                tolerance_match = re.search(r'marge de tolérance \((\d+) min\)', obj.description)
                expected_time_match = re.search(r'Heure prévue: ([\d:]+)', obj.description)
                actual_time_match = re.search(r'heure effective: ([\d:.]+)', obj.description)

                minutes = minutes_match.group(1) if minutes_match else ''
                tolerance = tolerance_match.group(1) if tolerance_match else ''
                expected_time = expected_time_match.group(1) if expected_time_match else ''
                actual_time = actual_time_match.group(1) if actual_time_match else ''

                if expected_time and actual_time:
                    return _('Late arrival of %(minutes)s minute(s) beyond the tolerance margin (%(tolerance)s min). Expected time: %(expected_time)s, actual time: %(actual_time)s.') % {
                        'minutes': minutes,
                        'tolerance': tolerance,
                        'expected_time': expected_time,
                        'actual_time': actual_time
                    }
                else:
                    return _('Late arrival of %(minutes)s minute(s) beyond the tolerance margin (%(tolerance)s min).') % {
                        'minutes': minutes,
                        'tolerance': tolerance
                    }

        elif obj.anomaly_type == Anomaly.AnomalyType.EARLY_DEPARTURE:
            if 'Départ anticipé de' in obj.description:
                # Extraire les informations numériques
                minutes_match = re.search(r'Départ anticipé de (\d+) minute\(s\)', obj.description)
                tolerance_match = re.search(r'marge de tolérance \((\d+) min\)', obj.description)
                expected_time_match = re.search(r'Heure prévue: ([\d:]+)', obj.description)
                actual_time_match = re.search(r'heure effective: ([\d:.]+)', obj.description)

                minutes = minutes_match.group(1) if minutes_match else ''
                tolerance = tolerance_match.group(1) if tolerance_match else ''
                expected_time = expected_time_match.group(1) if expected_time_match else ''
                actual_time = actual_time_match.group(1) if actual_time_match else ''

                if expected_time and actual_time:
                    return _('Early departure of %(minutes)s minute(s) beyond the tolerance margin (%(tolerance)s min). Expected time: %(expected_time)s, actual time: %(actual_time)s.') % {
                        'minutes': minutes,
                        'tolerance': tolerance,
                        'expected_time': expected_time,
                        'actual_time': actual_time
                    }
                else:
                    return _('Early departure of %(minutes)s minute(s) beyond the tolerance margin (%(tolerance)s min).') % {
                        'minutes': minutes,
                        'tolerance': tolerance
                    }
            elif 'Durée insuffisante:' in obj.description:
                # Extraire les informations numériques
                actual_duration_match = re.search(r'Durée insuffisante: ([\d.]+) minutes', obj.description)
                expected_duration_match = re.search(r'au lieu de ([\d.]+) minutes minimum', obj.description)
                tolerance_match = re.search(r'\(tolérance: (\d+)%\)', obj.description)

                actual_duration = actual_duration_match.group(1) if actual_duration_match else ''
                expected_duration = expected_duration_match.group(1) if expected_duration_match else ''
                tolerance = tolerance_match.group(1) if tolerance_match else ''

                return _('Insufficient duration: %(actual_duration)s minutes instead of %(expected_duration)s minutes minimum (tolerance: %(tolerance)s%%).') % {
                    'actual_duration': actual_duration,
                    'expected_duration': expected_duration,
                    'tolerance': tolerance
                }

        elif obj.anomaly_type == Anomaly.AnomalyType.MISSING_ARRIVAL:
            if 'Arrivée manquante selon le planning' in obj.description:
                expected_time_match = re.search(r'heure prévue: ([\d:]+)', obj.description)
                expected_time = expected_time_match.group(1) if expected_time_match else ''

                if expected_time:
                    return _('Missing arrival according to schedule (expected time: %(expected_time)s)') % {
                        'expected_time': expected_time
                    }
                else:
                    return _('Missing arrival according to schedule')
            elif 'Pointage manquant selon le planning fréquence' in obj.description:
                duration_match = re.search(r'durée prévue: (\d+) minutes', obj.description)
                duration = duration_match.group(1) if duration_match else ''

                return _('Missing check-in according to frequency schedule (expected duration: %(duration)s minutes)') % {
                    'duration': duration
                }

        elif obj.anomaly_type == Anomaly.AnomalyType.UNLINKED_SCHEDULE:
            return _('Check-in outside schedule: employee is not linked to this site.')

        elif obj.anomaly_type == Anomaly.AnomalyType.OTHER:
            if 'Pointage hors planning:' in obj.description:
                if 'aucun planning n\'est défini pour le jour' in obj.description:
                    day_match = re.search(r'jour ([^.]+)', obj.description)
                    entry_type_match = re.search(r'\(([^)]+) à', obj.description)
                    time_match = re.search(r'à ([\d:]+)\)', obj.description)

                    day = day_match.group(1) if day_match else ''
                    entry_type = entry_type_match.group(1) if entry_type_match else ''
                    time = time_match.group(1) if time_match else ''

                    return _('Check-in outside schedule: no schedule is defined for day %(day)s. (%(entry_type)s at %(time)s)') % {
                        'day': day,
                        'entry_type': entry_type,
                        'time': time
                    }
                elif 'l\'heure' in obj.description:
                    time_match = re.search(r'l\'heure ([\d:]+\.?\d*)', obj.description)
                    entry_type_match = re.search(r'\(([^)]+)\) ne correspond', obj.description)
                    ranges_match = re.search(r'Plages disponibles: ([^.]+)', obj.description)

                    time = time_match.group(1) if time_match else ''
                    entry_type = entry_type_match.group(1) if entry_type_match else ''
                    ranges = ranges_match.group(1) if ranges_match else ''

                    return _('Check-in outside schedule: time %(time)s (%(entry_type)s) does not match any time range defined in employee schedules. Available ranges: %(ranges)s.') % {
                        'time': time,
                        'entry_type': entry_type,
                        'ranges': ranges
                    }

        elif obj.anomaly_type == Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE:
            if 'Pointage' in obj.description and 'consécutif détecté' in obj.description:
                entry_type_match = re.search(r'Pointage ([^\s]+)', obj.description)
                last_time_match = re.search(r'Dernier pointage : ([\d:]+)', obj.description)

                entry_type = entry_type_match.group(1) if entry_type_match else ''
                last_time = last_time_match.group(1) if last_time_match else ''

                return _('Consecutive %(entry_type)s check-in detected. Last check-in: %(last_time)s') % {
                    'entry_type': entry_type,
                    'last_time': last_time
                }

        # Si aucun cas spécifique n'est trouvé, retourner la description originale
        return obj.description

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

