"""Perform data analysis with console output.

Run this script using `python manage.py simple_analysis`.
"""
import datetime

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
        df2 = df2.sort_values(by="current price")
        df2 = df2.sort_values(by="price change")

        self.stdout.write(self.style.SUCCESS(str(df2)))
        self.stdout.write(self.style.SUCCESS(str(df2["price change"].mean())))

    def get_month_price(self, df, model, months_before=0):
        # get current date
        today = datetime.date.today()

        # calculate target month
        target_date = today - datetime.timedelta(days=months_before * 30)
        target_year = target_date.year
        target_month = target_date.month

        # get month price data
        month_price = float(
            df[
                (df["gpu__model"] == model)
                & (df["year"] == target_year)
                & (df["month"] == target_month)
            ]["total_price"]
        )

        return month_price

    def proccess_gpu_model(self, df, new_df, model):
        last_month_price = self.get_month_price(df, model, months_before=2)
        this_month_price = self.get_month_price(df, model, months_before=1)
        new_df.append(
            {
                "model": model,
                "original price": last_month_price,
                "current price": this_month_price,
                "price change": (this_month_price - last_month_price)
                / last_month_price,
            }
        )
