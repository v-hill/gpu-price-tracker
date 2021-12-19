from django.contrib import admin

from .models import GraphicsCard, GraphicsCardLink, NvidiaGeneration


@admin.register(GraphicsCard)
class GraphicsCardAdmin(admin.ModelAdmin):
    list_display = (
        "model",
        "architecture",
        "launch_date",
        "launch_price",
        "memory_size",
        "ti",
        "super",
        "g3d_mark_median",
        "passmark_samples",
    )
    ordering = ["launch_date"]


@admin.register(NvidiaGeneration)
class NvidiaGenerationAdmin(admin.ModelAdmin):
    list_display = (
        "series",
        "architecture",
        "year",
    )
    ordering = ["id"]


@admin.register(GraphicsCardLink)
class GraphicsCardLinkAdmin(admin.ModelAdmin):
    list_display = (
        "model",
        "ebay_gpu",
    )
    ordering = ["model", "ebay_gpu"]
