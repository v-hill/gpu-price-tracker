"""Explicitly defined the primary key type."""
from django.apps import AppConfig


class VisualisationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "visualisation"
