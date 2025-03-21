from rest_framework import serializers
from .models import Alert

class AlertSerializer(serializers.ModelSerializer):
    """Serializer pour les alertes"""
    employee_name = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    alert_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
    
    def get_site_name(self, obj):
        return obj.site.name
    
    def get_alert_type_display(self, obj):
        return obj.get_alert_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()

