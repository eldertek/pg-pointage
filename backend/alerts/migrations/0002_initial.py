# Generated by Django 4.2.10 on 2025-03-26 17:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("timesheets", "0001_initial"),
        ("alerts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="anomaly",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="alerts",
                to="timesheets.anomaly",
                verbose_name="anomalie",
            ),
        ),
    ]
