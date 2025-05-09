# Generated by Django 4.2.10 on 2025-04-01 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timesheets', '0004_timesheet_scan_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timesheet',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=10, max_digits=12, null=True, verbose_name='latitude'),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=10, max_digits=12, null=True, verbose_name='longitude'),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='scan_type',
            field=models.CharField(choices=[('NFC', 'NFC'), ('QR_CODE', 'QR Code')], default='QR_CODE', max_length=10, verbose_name='type de scan'),
        ),
    ]
