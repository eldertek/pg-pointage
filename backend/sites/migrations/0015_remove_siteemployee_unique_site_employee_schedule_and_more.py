# Generated by Django 4.2.10 on 2025-04-10 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0014_remove_schedule_tolerance_margin'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='siteemployee',
            name='unique_site_employee_schedule',
        ),
        migrations.AddIndex(
            model_name='siteemployee',
            index=models.Index(fields=['site', 'employee', 'schedule'], name='sites_sitee_site_id_37760d_idx'),
        ),
    ]
