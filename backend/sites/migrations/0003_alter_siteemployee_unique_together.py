# Generated by Django 4.2.10 on 2025-03-24 22:18

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sites", "0002_schedule_allow_early_arrival_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="siteemployee",
            unique_together={("site", "employee", "schedule")},
        ),
    ]
