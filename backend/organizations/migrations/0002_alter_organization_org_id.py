# Generated by Django 4.2.10 on 2025-03-28 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='org_id',
            field=models.CharField(help_text="ID unique de l'organisation au format O + 3 chiffres", max_length=4, unique=True, verbose_name='ID Organisation'),
        ),
    ]
