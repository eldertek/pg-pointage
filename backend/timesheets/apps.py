from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class TimesheetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timesheets'
    verbose_name = _('Pointages')
    
    def ready(self):
        import timesheets.signals 