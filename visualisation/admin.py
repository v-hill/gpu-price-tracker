from django.contrib import admin

from .models import GraphicsCard, GraphicsCardLink, NvidiaGeneration, Sale


@admin.register(GraphicsCard)
class GraphicsCardAdmin(admin.ModelAdmin):
    list_display = (
        "model",
        "short_model",
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
    ordering = ["model__launch_date"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "gpu",
        "title",
        "date",
        "total_price",
        "outlier",
        "founders",
    )
    search_fields = ["title"]
    ordering = ["-date"]
