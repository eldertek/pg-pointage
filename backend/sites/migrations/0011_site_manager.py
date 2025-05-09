# Generated by Django 4.2.10 on 2025-04-01 19:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0010_remove_site_manager_schedule_employees_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='manager',
            field=models.ForeignKey(help_text='Manager responsable du site', limit_choices_to={'role': 'MANAGER'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_sites', to=settings.AUTH_USER_MODEL, verbose_name='manager'),
        ),
    ]
