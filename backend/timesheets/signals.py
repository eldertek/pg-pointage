from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .models import Anomaly
from alerts.models import Alert
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Anomaly)
def create_alert_for_anomaly(sender, instance, created, **kwargs):
    """Crée une alerte lorsqu'une anomalie est détectée"""
    if created:
        alert_type = instance.anomaly_type
        message = None
        alert_type_enum = None

        # Préparer le message et le type d'alerte en fonction du type d'anomalie
        if alert_type == Anomaly.AnomalyType.CONSECUTIVE_SAME_TYPE:
            message = _(
                f'Anomalie détectée : Pointages consécutifs du même type\n'
                f'Employé : {instance.employee.get_full_name()}\n'
                f'Site : {instance.site.name}\n'
                f'Date : {instance.date}\n'
                f'Description : {instance.description}'
            )
            alert_type_enum = Alert.AlertType.CONSECUTIVE_SAME_TYPE

        elif alert_type == Anomaly.AnomalyType.LATE:
            # Vérifier si le retard dépasse la marge
            site = instance.site
            if instance.schedule:
                schedule = instance.schedule
                late_margin = schedule.late_arrival_margin or site.late_margin
            else:
                late_margin = site.late_margin

            # Ne créer une alerte que si le retard dépasse la marge
            if instance.minutes > late_margin:
                message = _(
                    f'Anomalie détectée : Retard\n'
                    f'Employé : {instance.employee.get_full_name()}\n'
                    f'Site : {instance.site.name}\n'
                    f'Date : {instance.date}\n'
                    f'Minutes de retard : {instance.minutes}\n'
                    f'Description : {instance.description}'
                )
                alert_type_enum = Alert.AlertType.LATE
            else:
                # Ne pas créer d'alerte pour les retards dans la marge
                logger.info(f"Pas d'alerte créée pour le retard de {instance.minutes} minutes car il est dans la marge de {late_margin} minutes.")
                message = None
                alert_type_enum = None

        elif alert_type == Anomaly.AnomalyType.EARLY_DEPARTURE:
            # Vérifier si le départ anticipé dépasse la marge
            site = instance.site
            if instance.schedule:
                schedule = instance.schedule
                early_departure_margin = schedule.early_departure_margin or site.early_departure_margin
            else:
                early_departure_margin = site.early_departure_margin

            # Ne créer une alerte que si le départ anticipé dépasse la marge
            if instance.minutes > early_departure_margin:
                message = _(
                    f'Anomalie détectée : Départ anticipé\n'
                    f'Employé : {instance.employee.get_full_name()}\n'
                    f'Site : {instance.site.name}\n'
                    f'Date : {instance.date}\n'
                    f'Minutes de départ anticipé : {instance.minutes}\n'
                    f'Description : {instance.description}'
                )
                alert_type_enum = Alert.AlertType.EARLY_DEPARTURE
            else:
                # Ne pas créer d'alerte pour les départs anticipés dans la marge
                logger.info(f"Pas d'alerte créée pour le départ anticipé de {instance.minutes} minutes car il est dans la marge de {early_departure_margin} minutes.")
                message = None
                alert_type_enum = None

        elif alert_type == Anomaly.AnomalyType.MISSING_ARRIVAL:
            message = _(
                f'Anomalie détectée : Arrivée manquante\n'
                f'Employé : {instance.employee.get_full_name()}\n'
                f'Site : {instance.site.name}\n'
                f'Date : {instance.date}\n'
                f'Description : {instance.description}'
            )
            alert_type_enum = Alert.AlertType.MISSING_ARRIVAL

        elif alert_type == Anomaly.AnomalyType.MISSING_DEPARTURE:
            message = _(
                f'Anomalie détectée : Départ manquant\n'
                f'Employé : {instance.employee.get_full_name()}\n'
                f'Site : {instance.site.name}\n'
                f'Date : {instance.date}\n'
                f'Description : {instance.description}'
            )
            alert_type_enum = Alert.AlertType.MISSING_DEPARTURE

        elif alert_type == Anomaly.AnomalyType.INSUFFICIENT_HOURS:
            message = _(
                f'Anomalie détectée : Heures insuffisantes\n'
                f'Employé : {instance.employee.get_full_name()}\n'
                f'Site : {instance.site.name}\n'
                f'Date : {instance.date}\n'
                f'Minutes manquantes : {instance.minutes}\n'
                f'Description : {instance.description}'
            )
            alert_type_enum = Alert.AlertType.INSUFFICIENT_HOURS

        elif alert_type == Anomaly.AnomalyType.OTHER:
            message = _(
                f'Anomalie détectée : Autre\n'
                f'Employé : {instance.employee.get_full_name()}\n'
                f'Site : {instance.site.name}\n'
                f'Date : {instance.date}\n'
                f'Description : {instance.description}'
            )
            alert_type_enum = Alert.AlertType.OTHER

        # Créer l'alerte si un message et un type ont été définis
        if message and alert_type_enum:
            logger.info(f"Création d'une alerte pour l'anomalie {instance.id} de type {alert_type}")
            Alert.objects.create(
                employee=instance.employee,
                site=instance.site,
                anomaly=instance,
                alert_type=alert_type_enum,
                message=message,
                recipients=instance.site.alert_emails,
                status=Alert.AlertStatus.PENDING
            )
        else:
            logger.warning(f"Impossible de créer une alerte pour l'anomalie {instance.id} de type {alert_type} : type non géré")