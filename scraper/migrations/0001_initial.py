# Generated by Django 3.2.10 on 2021-12-19 10:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Log",
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
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                (
                    "sales_scraped",
                    models.IntegerField(
                        help_text="Number of products scraped during the run."
                    ),
                ),
                (
                    "sales_added",
                    models.IntegerField(
                        help_text=(
                            "Number of products added to the database during"
                            " the run."
                        )
                    ),
                ),
            ],
        ),
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
                    models.FloatField(verbose_name="Memory size (MB)"),
                ),
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
                        to="scraper.nvidiageneration",
                    ),
                ),
            ],
            options={
                "unique_together": {("model",)},
            },
        ),
        migrations.CreateModel(
            name="EbayGraphicsCard",
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
                ("name", models.CharField(max_length=80)),
                ("collect_data", models.BooleanField(default=True)),
                ("data_collected", models.BooleanField()),
                ("last_collection", models.DateTimeField()),
                (
                    "total_collected",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.log",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.graphicscard",
                    ),
                ),
            ],
            options={
                "unique_together": {("name",)},
            },
        ),
        migrations.CreateModel(
            name="URL",
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
                ("url", models.CharField(max_length=200)),
                (
                    "gpu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.ebaygraphicscard",
                    ),
                ),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.log",
                    ),
                ),
            ],
            options={
                "unique_together": {("url", "log", "gpu")},
            },
        ),
        migrations.CreateModel(
            name="Sale",
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
                ("title", models.CharField(max_length=80)),
                ("bids", models.IntegerField()),
                ("date", models.DateTimeField()),
                ("postage", models.FloatField()),
                ("price", models.FloatField()),
                ("total_price", models.FloatField()),
                (
                    "gpu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.ebaygraphicscard",
                    ),
                ),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.log",
                    ),
                ),
            ],
            options={
                "unique_together": {
                    ("gpu", "title", "date", "bids", "price", "postage")
                },
            },
        ),
        migrations.CreateModel(
            name="BrandMenu",
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
                ("text", models.CharField(max_length=80)),
                ("button_id", models.CharField(max_length=80)),
                (
                    "log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scraper.log",
                    ),
                ),
            ],
            options={
                "unique_together": {("text",)},
            },
        ),
    ]