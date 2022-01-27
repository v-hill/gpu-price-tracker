# Generated by Django 3.2.10 on 2021-12-24 15:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("visualisation", "0003_auto_20211219_1634"),
    ]

    operations = [
        migrations.AddField(
            model_name="graphicscard",
            name="short_model",
            field=models.CharField(default=1000, max_length=20),
            preserve_default=False,
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
                ("date", models.DateTimeField()),
                ("total_price", models.FloatField()),
                ("outlier", models.BooleanField(default=False)),
                ("founders", models.BooleanField(default=False)),
                (
                    "gpu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="visualisation.graphicscard",
                    ),
                ),
            ],
            options={
                "unique_together": {("gpu", "title", "date", "total_price")},
            },
        ),
    ]