"""
Run this script using `python manage.py export_to_csv`
"""
from django.core.management.base import BaseCommand
from visualisation.models import GraphicsCard, Sale
import csv


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--model",
            type=str,
            help="Name of the GPU model to export",
            required=True,
        )

    def handle(self, *args, **kwargs):
        model_search = kwargs["model"]
        matching_gpus = GraphicsCard.objects.filter(
            model__icontains=model_search
        )

        if matching_gpus.count() == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"No GPU models found matching search: '{model_search}'"
                )
            )

        elif matching_gpus.count() > 1:
            self.stdout.write(
                self.style.WARNING(
                    "Multiple GPU models found matching search:"
                    f" '{model_search}'"
                )
            )
            matching_gpus = [gpu["model"] for gpu in matching_gpus]
            for gpu in matching_gpus:
                self.stdout.write(f"    - {gpu}")

            self.stdout.write(
                self.style.WARNING("Please repeat with a more detailed search")
            )

        else:
            self.stdout.write(f"Selected GPU: {matching_gpus[0]}")
            query_set = Sale.objects.filter(gpu__model=matching_gpus[0])
            self.stdout.write(f"{query_set.count()} sales found")

            output = []
            for card in query_set:
                output.append(
                    [
                        card.title,
                        card.date.strftime("%Y-%m-%d"),
                        card.total_price,
                        card.outlier,
                        card.founders,
                    ]
                )

            with open(
                f"{matching_gpus[0]}.csv",
                "w",
                encoding="utf-8",
                newline="",
            ) as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow(
                    [
                        "Title",
                        "Date",
                        "Total price",
                        "Outlier",
                        "Founders",
                    ]
                )

                # CSV data
                writer.writerows(output)
            self.stdout.write(self.style.SUCCESS("Done"))
