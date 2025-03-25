from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .models import Anomaly
from alerts.models import Alert

@receiver(post_save, sender=Anomaly)
def create_alert_for_anomaly(sender, instance, created, **kwargs):
    """Crée une alerte lorsqu'une anomalie est détectée"""
    if created:
        alert_type = instance.anomaly_type
        if alert_type == Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE:
            message = _(
                f'Anomalie détectée : Pointages consécutifs du même type\n'
                f'Employé : {instance.employee.get_full_name()}\n'
                f'Site : {instance.site.name}\n'
                f'Date : {instance.date}\n'
                f'Description : {instance.description}'
            )
            
            Alert.objects.create(
                employee=instance.employee,
                site=instance.site,
                anomaly=instance,
                alert_type=Alert.AlertType.CONSECUTIVE_SAME_TYPE,
                message=message,
                recipients=instance.site.alert_emails,
                status=Alert.AlertStatus.PENDING
            ) 