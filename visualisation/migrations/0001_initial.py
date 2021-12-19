# Generated by Django 3.2.10 on 2021-12-19 15:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("scraper", "0002_auto_20211219_1553"),
    ]

    operations = [
        migrations.CreateModel(
            name="NvidiaGeneration",
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
                ("architecture", models.CharField(max_length=80)),
                ("series", models.CharField(max_length=80)),
                ("year", models.IntegerField(verbose_name="Release year")),
            ],
            options={
                "unique_together": {("architecture", "series")},
            },
        ),
        migrations.CreateModel(
            name="GraphicsCard",
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
                ("model", models.CharField(max_length=80)),
                ("launch_date", models.DateField()),
                (
                    "launch_price",
                    models.IntegerField(verbose_name="Launch price (£)"),
                ),
                (
                    "memory_size",
                    models.IntegerField(verbose_name="Memory size (MB)"),
                ),
                ("memory_size_restrict", models.BooleanField(default=False)),
                ("ti", models.BooleanField(default=False)),
                ("ti_restrict", models.BooleanField(default=False)),
                (
                    "tdp",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="TDP (Watts)"
                    ),
                ),
                (
                    "g3d_mark_median",
                    models.IntegerField(verbose_name="G3DMark median score"),
                ),
                ("passmark_samples", models.IntegerField()),
                (
                    "architecture",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="visualisation.nvidiageneration",
                    ),
                ),
            ],
            options={
                "unique_together": {("model",)},
            },
        ),
        migrations.CreateModel(
            name="GraphicsCardLink",
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
                    "ebay_gpu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.ebaygraphicscard",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="visualisation.graphicscard",
                    ),
                ),
            ],
            options={
                "unique_together": {("model", "ebay_gpu")},
            },
        ),
    ]
