"""Perform data analysis with console output.

Run this script using `python manage.py simple_analysis`.
"""
import pandas as pd
from django.core.management.base import BaseCommand

from visualisation.models import Sale


class Command(BaseCommand):
    help = "Perform simple data analysis to be printed to stdout."

    def handle(self, *args, **kwargs):
        df = pd.DataFrame(
            Sale.objects.filter(founders=False).values(
                "gpu__model",
                "date",
                "total_price",
            )
        )

        df["month"] = pd.DatetimeIndex(df["date"]).month
        df["year"] = pd.DatetimeIndex(df["date"]).year
        print(df.shape)

        df = df.groupby(["year", "month", "gpu__model"]).median().reset_index()

        new_df = []
        for model in df["gpu__model"].unique():
            self.proccess_gpu_model(df, new_df, model)

        df2 = pd.DataFrame(new_df)
        df2 = df2.sort_values(by="price change")
        df2 = df2.sort_values(by="current price")

        self.stdout.write(self.style.SUCCESS(str(df2)))

    def proccess_gpu_model(self, df, new_df, model):
        september_price = float(
            df[
                (df["gpu__model"] == model)
                & (df["year"] == 2022)
                & (df["month"] == 9)
            ]["total_price"]
        )
        october_price = float(
            df[
                (df["gpu__model"] == model)
                & (df["year"] == 2022)
                & (df["month"] == 10)
            ]["total_price"]
        )
        new_df.append(
            {
                "model": model,
                "original price": september_price,
                "current price": october_price,
                "price change": (october_price - september_price)
                / september_price,
            }
        )
