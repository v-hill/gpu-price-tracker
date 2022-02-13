"""
Run this script using `python manage.py generate_clean_sales`
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from scraper.models import EbayGraphicsCard
from scraper.models import Sale as OriginalSale
from visualisation.models import GraphicsCard, GraphicsCardLink, Sale


class Command(BaseCommand):
    help = (
        "Populate the visualisation app Sale table with cleaned data, based on"
        "the GraphicsCardLink table definitions."
    )

    def handle(self, *args, **kwargs):
        Sale.objects.all().delete()
        exclusions_list = [
            "bitcoin",
            "box only",
            "damaged",
            "fake",
            "faulty",
            "intelnew",
            "parts only",
            "repair",
            "ryzen",
        ]
        general_exclusions = Q()
        for ti_strings in exclusions_list:
            general_exclusions |= Q(title__icontains=ti_strings)

        ti_q = Q()
        for ti_strings in ["0Ti", " Ti"]:
            ti_q |= Q(title__icontains=ti_strings)

        qs = GraphicsCardLink.objects.all()

        for link in qs:
            self.stdout.write(f"{link}")
            card = GraphicsCard.objects.filter(pk=link.model_id).first()
            ebay_card = EbayGraphicsCard.objects.filter(
                pk=link.ebay_gpu_id
            ).first()
            sales_qs = OriginalSale.objects.filter(gpu_id=ebay_card.id)

            filtered_qs = sales_qs.filter(title__icontains=card.short_model)
            if card.memory_size_restrict:
                memory_gb = int(card.memory_size / 1000)
                self.stdout.write(
                    f"    filtering by memory size: {memory_gb} GB"
                )
                memory_q = Q()
                for memory_strings in [f"{memory_gb} GB", f"{memory_gb}GB"]:
                    memory_q |= Q(title__icontains=memory_strings)
                filtered_qs = filtered_qs.filter(memory_q)
            if card.ti_restrict:
                self.stdout.write(f"    filtering by Ti: {card.ti}")
                if card.ti:
                    filtered_qs = filtered_qs.filter(ti_q)
                    filtered_qs = filtered_qs.exclude(
                        title__icontains="not ti"
                    )
                else:
                    filtered_qs = filtered_qs.exclude(ti_q)
            if card.super_restrict:
                self.stdout.write(f"    filtering by Super: {card.super}")
                if card.super:
                    filtered_qs = filtered_qs.filter(title__icontains="super")
                    filtered_qs = filtered_qs.exclude(
                        title__icontains="not super"
                    )

                else:
                    filtered_qs = filtered_qs.exclude(title__icontains="super")
            filtered_qs = filtered_qs.exclude(general_exclusions)

            filtered_qs = filtered_qs.exclude(title__iregex=r"^.{,7}$")

            # for item in filtered_qs.values().order_by("-total_price")[:5]:
            #     print(f"    £{item['total_price']:>5} | {item['title']}")

            new_sales = []
            for item in filtered_qs.values():
                if "founder" in item["title"].lower():
                    new_sale = Sale(
                        gpu=card,
                        title=item["title"],
                        date=item["date"],
                        total_price=item["total_price"],
                        outlier=False,
                        founders=True,
                    )
                else:
                    new_sale = Sale(
                        gpu=card,
                        title=item["title"],
                        date=item["date"],
                        total_price=item["total_price"],
                        outlier=False,
                        founders=False,
                    )
                new_sales.append(new_sale)
            Sale.objects.bulk_create(new_sales)
            self.stdout.write(
                self.style.SUCCESS(
                    f"    {filtered_qs.count()} / {sales_qs.count()} sales"
                    " added"
                )
            )
