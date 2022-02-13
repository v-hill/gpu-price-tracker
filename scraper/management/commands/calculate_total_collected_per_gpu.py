"""
Run this script using `python manage.py calculate_total_collected_per_gpu`
"""
from django.core.management.base import BaseCommand

from scraper.models import EbayGraphicsCard, Sale


class Command(BaseCommand):
    help = (
        "Calculates the number of sales collected for each GPU in the"
        " EbayGraphicsCard table."
    )

    def handle(self, *args, **kwargs):
        self.stdout.write(
            "Calculating total_collected value for each GPU in the"
            " EbayGraphicsCard table..."
        )

        qs = EbayGraphicsCard.objects.all().order_by("-total_collected")
        for card in qs:
            count = Sale.objects.filter(gpu__id=card.id).count()
            card.total_collected = count
            card.save()
            self.stdout.write(f"{card.name:>44} | {count}")

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully calculated number of sales collected for each"
                " GPU in the database!"
            )
        )
