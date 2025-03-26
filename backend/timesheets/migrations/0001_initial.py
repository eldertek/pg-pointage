# Generated by Django 4.2.10 on 2025-03-26 17:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Anomaly",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(verbose_name="date")),
                (
                    "anomaly_type",
                    models.CharField(
                        choices=[
                            ("LATE", "Retard"),
                            ("EARLY_DEPARTURE", "Départ anticipé"),
                            ("MISSING_ARRIVAL", "Arrivée manquante"),
                            ("MISSING_DEPARTURE", "Départ manquant"),
                            ("INSUFFICIENT_HOURS", "Heures insuffisantes"),
                            (
                                "CONSECUTIVE_SAME_TYPE",
                                "Pointages consécutifs du même type",
                            ),
                            ("OTHER", "Autre"),
                        ],
                        max_length=30,
                        verbose_name="type d'anomalie",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "En attente"),
                            ("RESOLVED", "Résolu"),
                            ("IGNORED", "Ignoré"),
                        ],
                        default="PENDING",
                        max_length=20,
                        verbose_name="statut",
                    ),
                ),
                (
                    "minutes",
                    models.PositiveIntegerField(default=0, verbose_name="minutes"),
                ),
                (
                    "correction_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="date de correction"
                    ),
                ),
                (
                    "correction_note",
                    models.TextField(blank=True, verbose_name="note de correction"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
                ),
            ],
            options={
                "verbose_name": "anomalie",
                "verbose_name_plural": "anomalies",
                "ordering": ["-date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="EmployeeReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_date", models.DateField(verbose_name="date de début")),
                ("end_date", models.DateField(verbose_name="date de fin")),
                (
                    "total_hours",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=6,
                        verbose_name="heures totales",
                    ),
                ),
                (
                    "late_count",
                    models.PositiveIntegerField(
                        default=0, verbose_name="nombre de retards"
                    ),
                ),
                (
                    "total_late_minutes",
                    models.PositiveIntegerField(
                        default=0, verbose_name="minutes totales de retard"
                    ),
                ),
                (
                    "early_departure_count",
                    models.PositiveIntegerField(
                        default=0, verbose_name="nombre de départs anticipés"
                    ),
                ),
                (
                    "total_early_departure_minutes",
                    models.PositiveIntegerField(
                        default=0, verbose_name="minutes totales de départ anticipé"
                    ),
                ),
                (
                    "anomaly_count",
                    models.PositiveIntegerField(
                        default=0, verbose_name="nombre d'anomalies"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
                ),
            ],
            options={
                "verbose_name": "rapport d'employé",
                "verbose_name_plural": "rapports d'employés",
                "ordering": ["-end_date"],
            },
        ),
        migrations.CreateModel(
            name="Timesheet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="horodatage"
                    ),
                ),
                (
                    "entry_type",
                    models.CharField(
                        choices=[("ARRIVAL", "Arrivée"), ("DEPARTURE", "Départ")],
                        max_length=20,
                        verbose_name="type d'entrée",
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=10,
                        max_digits=13,
                        null=True,
                        verbose_name="latitude",
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=10,
                        max_digits=13,
                        null=True,
                        verbose_name="longitude",
                    ),
                ),
                (
                    "is_late",
                    models.BooleanField(default=False, verbose_name="en retard"),
                ),
                (
                    "late_minutes",
                    models.PositiveIntegerField(
                        default=0, verbose_name="minutes de retard"
                    ),
                ),
                (
                    "is_early_departure",
                    models.BooleanField(default=False, verbose_name="départ anticipé"),
                ),
                (
                    "early_departure_minutes",
                    models.PositiveIntegerField(
                        default=0, verbose_name="minutes de départ anticipé"
                    ),
                ),
                (
                    "is_out_of_schedule",
                    models.BooleanField(default=False, verbose_name="hors planning"),
                ),
                (
                    "is_ambiguous",
                    models.BooleanField(default=False, verbose_name="pointage ambigu"),
                ),
                (
                    "created_offline",
                    models.BooleanField(default=False, verbose_name="créé hors ligne"),
                ),
                (
                    "synced_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="synchronisé le"
                    ),
                ),
                (
                    "geolocation_enabled",
                    models.BooleanField(
                        default=True, verbose_name="géolocalisation activée"
                    ),
                ),
                (
                    "correction_note",
                    models.TextField(blank=True, verbose_name="note de correction"),
                ),
                (
                    "correction_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="date de correction"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
                ),
            ],
            options={
                "verbose_name": "pointage",
                "verbose_name_plural": "pointages",
                "ordering": ["-timestamp"],
            },
        ),
    ]
