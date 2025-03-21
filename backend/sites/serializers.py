from rest_framework import serializers
from .models import Site, Schedule, ScheduleDetail, SiteEmployee

class SiteSerializer(serializers.ModelSerializer):
    """Serializer pour les sites"""
    class Meta:
        model = Site
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails de planning"""
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleDetail
        fields = ['id', 'schedule', 'day_of_week', 'day_name', 'start_time_1', 'end_time_1', 
                'start_time_2', 'end_time_2']
    
    def get_day_name(self, obj):
        return obj.get_day_of_week_display()

class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer pour les plannings"""
    details = ScheduleDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'site', 'name', 'schedule_type', 'min_daily_hours', 
                'min_weekly_hours', 'created_at', 'updated_at', 'is_active', 'details']
        read_only_fields = ['created_at', 'updated_at']

class SiteEmployeeSerializer(serializers.ModelSerializer):
    """Serializer pour les employés du site"""
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SiteEmployee
        fields = ['id', 'site', 'employee', 'employee_name', 'schedule', 'created_at', 'is_active']
        read_only_fields = ['created_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username

