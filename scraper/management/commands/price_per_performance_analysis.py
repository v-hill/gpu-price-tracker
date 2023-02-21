"""Perform data analysis with console output.

Run this script using `python manage.py price_per_performance_analysis`.
"""
import pandas as pd
from django.core.management.base import BaseCommand

from visualisation import models as vis_models


class Command(BaseCommand):
    help = "Perform simple data analysis to be printed to stdout."

    def handle(self, *args, **kwargs):
        df = pd.DataFrame(
            vis_models.Sale.objects.filter(founders=False).values(
                "gpu__model",
                "date",
                "total_price",
            )
        )

        df["month"] = pd.DatetimeIndex(df["date"]).month
        df["year"] = pd.DatetimeIndex(df["date"]).year

        df = df.groupby(["year", "month", "gpu__model"]).mean().reset_index()

        new_df = []
        for model in df["gpu__model"].unique():
            self.proccess_gpu_model(df, new_df, model)

        df2 = pd.DataFrame(new_df)
        df2 = df2.sort_values(by="price/performance")

        self.stdout.write(self.style.SUCCESS(str(df2)))

    def proccess_gpu_model(self, df, new_df, model):
        month_price = float(
            df[
                (df["gpu__model"] == model)
                & (df["year"] == 2023)
                & (df["month"] == 1)
            ]["total_price"]
        )

        model = vis_models.GraphicsCard.objects.get(model=model)
        benchmark = int(model.g3d_mark_median)
        new_df.append(
            {
                "model": model,
                "current price": month_price,
                "g3d mark median": benchmark,
                "passmark samples": model.g3d_mark_median,
                "price/performance": month_price / benchmark,
            }
        )
