from django.utils import timezone
from zoneinfo import ZoneInfo
from .base import logger

class DateService:
    """
    Service de gestion des dates et des fuseaux horaires
    """
    @staticmethod
    def to_paris_timezone(date):
        """
        Convertit une date dans le fuseau horaire de Paris
        
        Args:
            date: La date à convertir
            
        Returns:
            La date convertie dans le fuseau horaire de Paris
        """
        logger.debug(f"[TRACKING DATE] to_paris_timezone - Date entrée: {date} (timezone: {date.tzinfo})")
        if timezone.is_naive(date):
            logger.debug("[TRACKING DATE] Date naïve détectée, ajout de la timezone")
            date = timezone.make_aware(date)
        result = timezone.localtime(date, timezone=ZoneInfo("Europe/Paris"))
        logger.debug(f"[TRACKING DATE] Date convertie Paris: {result} (timezone: {result.tzinfo}, offset: {result.utcoffset()})")
        return result 