from django.contrib import admin

from .models import URL, BrandMenu, EbayGraphicsCard, Log, Sale


class EbayGraphicsCardInline(admin.TabularInline):
    model = EbayGraphicsCard
    fields = ["collect_data", "total_collected", "last_collection"]
    readonly_fields = [
        "total_collected",
        # "collect_data",
        # "data_collected",
        "last_collection",
        # "log",
    ]
    ordering = ["-total_collected"]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "start_time",
        "end_time",
        "run_time",
        "sales_scraped",
        "sales_added",
    )
    ordering = ["-start_time"]
    inlines = [EbayGraphicsCardInline]


@admin.register(BrandMenu)
class BrandMenuAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "first_log",
        "latest_log",
    )
    search_fields = ["text"]
    ordering = ["text"]


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "url",
        "log",
        "gpu",
    )
    ordering = ["log", "gpu"]
    search_fields = ["gpu"]


class SaleInline(admin.TabularInline):
    model = Sale
    fields = [
        "log",
        "gpu",
        "title",
        "bids",
        "date",
        "postage",
        "price",
        "total_price",
    ]
    readonly_fields = [
        "log",
        "gpu",
        "title",
        "bids",
        "date",
        "postage",
        "price",
        "total_price",
    ]
    ordering = ["-date", "title"]


@admin.register(EbayGraphicsCard)
class EbayGraphicsCardAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "total_collected",
        "collect_data",
        "data_collected",
        "last_collection",
        "log",
    )
    search_fields = ["name"]
    ordering = ["-total_collected", "name"]
    inlines = [SaleInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "log",
        "gpu",
        "title",
        "bids",
        "date",
        "postage",
        "price",
        "total_price",
    )
    search_fields = ["title"]
    ordering = ["-date"]
