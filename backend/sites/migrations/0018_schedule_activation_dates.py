from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0017_site_activation_end_date_site_activation_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='activation_start_date',
            field=models.DateField(
                _('date de début d\'activation'),
                help_text='Date à partir de laquelle le planning sera actif',
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='schedule',
            name='activation_end_date',
            field=models.DateField(
                _('date de fin d\'activation'),
                help_text='Date à partir de laquelle le planning sera inactif',
                null=True,
                blank=True,
            ),
        ),
    ] 