"""Export the data for a specified GPU to a csv file.

Run this script using `python manage.py monthly_box_plot`
"""
import csv
import pandas as pd
import pandas as pd
import numpy as np
import seaborn
import matplotlib.pyplot as plt

from django.core.management.base import BaseCommand

from visualisation.models import GraphicsCard, Sale


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
                    "Multiple GPU models found matching search"
                    f" '{model_search}':"
                )
            )
            matching_gpus_models = [gpu.model for gpu in matching_gpus]
            for gpu in matching_gpus_models:
                self.stdout.write(f"  - {gpu}")
            gpu_selected = min(matching_gpus_models, key=len)
            gpu_selected = matching_gpus.filter(model=gpu_selected).first()
        else:
            gpu_selected = matching_gpus[0]

        qs = Sale.objects.filter(
            founders=False,
            gpu__model=gpu_selected.model,
        )

        df = pd.DataFrame(qs.values("date", "total_price"))
        df.sort_values(by="date", inplace=True)

        df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))

        fig, ax = plt.subplots()
        fig.set_size_inches((12,4))
        box_plot = seaborn.boxplot(x='month',y='total_price',data=df,ax=ax)

        medians = df.groupby(['month'])['total_price'].median().round(2)
        vertical_offset = df['total_price'].median() * 0.05 # offset from median for display

        for xtick in box_plot.get_xticks():
            box_plot.text(xtick,medians[xtick] + vertical_offset,medians[xtick], 
                    horizontalalignment='center',size='small',color='b',weight='semibold')

        plt.show()

        self.stdout.write(self.style.SUCCESS(f"Selected GPU: {gpu_selected}"))
