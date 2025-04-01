# Generated by Django 4.2.10 on 2025-04-01 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_remove_report_name_alter_report_created_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='name',
            field=models.CharField(default='...', max_length=255, verbose_name='nom'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='report',
            name='report_format',
            field=models.CharField(choices=[('PDF', 'PDF'), ('CSV', 'CSV'), ('EXCEL', 'Excel')], default='PDF', max_length=10, verbose_name='format du rapport'),
        ),
        migrations.AlterField(
            model_name='report',
            name='report_type',
            field=models.CharField(choices=[('DAILY', 'Journalier'), ('WEEKLY', 'Hebdomadaire'), ('MONTHLY', 'Mensuel')], max_length=20, verbose_name='type de rapport'),
        ),
    ]
