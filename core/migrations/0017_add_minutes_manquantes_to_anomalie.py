# Generated by Django 5.1.5 on 2025-03-18 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_more_missing_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$ 
            BEGIN
                -- Ajouter minutes_manquantes à Anomalie
                BEGIN
                    ALTER TABLE core_anomalie ADD COLUMN minutes_manquantes integer DEFAULT 0;
                EXCEPTION
                    WHEN duplicate_column THEN NULL;
                END;
            END $$;
            """,
            reverse_sql="""
            ALTER TABLE core_anomalie DROP COLUMN IF EXISTS minutes_manquantes;
            """
        ),
    ] 