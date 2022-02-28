"""
Run this script using `python manage.py generate_clean_total_sales`
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models import Count

from scraper.models import EbayGraphicsCard
from scraper.models import Sale as OriginalSale
from visualisation.models import GraphicsCard, GraphicsCardLink, Sale
import pandas as pd


class Command(BaseCommand):
    help = (
        "From the visualisation app Sale table (with cleaned data), calculate"
        " the total number of sales per GPU model"
    )

    def handle(self, *args, **kwargs):

        result = pd.DataFrame(
            Sale.objects.filter(founders=True).values("gpu__model")
            .annotate(count=Count("gpu"))
            .order_by("-count")[:20]
        )

        self.stdout.write(self.style.SUCCESS(str(result)))
