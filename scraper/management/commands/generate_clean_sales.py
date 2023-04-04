"""Populate the visualisation app Sale table with cleaned data.

Run this script using `python manage.py generate_clean_sales`
"""
import pandas as pd
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
        exclusions_list = self.title_excluded_strings()
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
            sales_qs, filtered_qs = self.get_filtered_queryset(
                general_exclusions, ti_q, link, card
            )
            if filtered_qs.count() == 0:
                continue

            df = pd.DataFrame(
                filtered_qs.values("date", "title", "total_price")
            )
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(by="date").reset_index()
            df_rolling = self.get_rolling_prices(df)

            df = df.merge(df_rolling, on="date", how="left")

            df = self.remove_outliers(df)
            new_sales = self.create_sale_objects(card, df)
            Sale.objects.bulk_create(new_sales)
            self.stdout.write(
                self.style.SUCCESS(
                    f"    {len(new_sales)} / {sales_qs.count()} sales added"
                )
            )

    def create_sale_objects(self, card, df):
        new_sales = []
        for index, item in df.iterrows():
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
        return new_sales

    def remove_outliers(self, df, outlier_threshold=3):
        # set flag for upper outliers
        df.loc[
            (
                df["total_price"]
                > df["rolling price mean"]
                + (df["rolling price stdev"]) * outlier_threshold
            )
            & (df["rolling price stdev"] > 0),
            "outlier",
        ] = 1

        # set flag for lower outliers
        df.loc[
            (
                df["total_price"]
                < df["rolling price mean"]
                - (df["rolling price stdev"]) * outlier_threshold
            )
            & (df["rolling price stdev"] > 0),
            "outlier",
        ] = 1

        df["outlier"] = df["outlier"].fillna(value=0)

        num_outliers = int(df["outlier"].sum())
        self.stdout.write(
            f"    {num_outliers} / {df.shape[0]} outliers removed -"
            f" {num_outliers/df.shape[0]:0.1%}"
        )
        df = df[df["outlier"] == 0]
        return df

    def get_filtered_queryset(self, general_exclusions, ti_q, link, card):
        ebay_card = EbayGraphicsCard.objects.filter(
            pk=link.ebay_gpu_id
        ).first()
        sales_qs = OriginalSale.objects.filter(gpu_id=ebay_card.id)

        filtered_qs = sales_qs.filter(title__icontains=card.short_model)
        if card.memory_size_restrict:
            memory_gb = int(card.memory_size / 1000)
            self.stdout.write(f"    filtering by memory size: {memory_gb} GB")
            memory_q = Q()
            for memory_strings in [f"{memory_gb} GB", f"{memory_gb}GB"]:
                memory_q |= Q(title__icontains=memory_strings)
            filtered_qs = filtered_qs.filter(memory_q)
        if card.ti_restrict:
            self.stdout.write(f"    filtering by Ti: {card.ti}")
            if card.ti:
                filtered_qs = filtered_qs.filter(ti_q)
                filtered_qs = filtered_qs.exclude(title__icontains="not ti")
            else:
                filtered_qs = filtered_qs.exclude(ti_q)
        if card.super_restrict:
            self.stdout.write(f"    filtering by Super: {card.super}")
            if card.super:
                filtered_qs = filtered_qs.filter(title__icontains="super")
                filtered_qs = filtered_qs.exclude(title__icontains="not super")

            else:
                filtered_qs = filtered_qs.exclude(title__icontains="super")
        filtered_qs = filtered_qs.exclude(general_exclusions)

        filtered_qs = filtered_qs.exclude(title__iregex=r"^.{,7}$")
        return sales_qs, filtered_qs

    def title_excluded_strings(self):
        """Return a list of strings which are to be excluded from titles.

        Any item with a title that contains one or more of the following
        strings is to be excluded from the cleaned sales data.
        """
        exclusions_list = [
            "bitcoin",
            "mining",
            "box only",
            "damaged",
            "fake",
            "faulty",
            "intel",
            "parts only",
            "repair",
            "needs",
            "but",
            "ryzen",
            "empty",
        ]

        return exclusions_list

    def get_rolling_prices(self, df):
        df_date_grouped = (
            df.groupby("date")["total_price"].mean().reset_index()
        )
        df_date_grouped = df_date_grouped.set_index("date")
        rolling_stdev = df_date_grouped.rolling(14, min_periods=7).std()
        rolling_stdev["date"] = rolling_stdev.index
        rolling_stdev = rolling_stdev.rename(
            columns={"total_price": "rolling price stdev"}
        )
        rolling_stdev = rolling_stdev.reset_index(drop=True)

        rolling_mean = df_date_grouped.rolling(7, min_periods=1).mean()
        rolling_mean["date"] = rolling_mean.index
        rolling_mean = rolling_mean.rename(
            columns={"total_price": "rolling price mean"}
        )
        rolling_mean = rolling_mean.reset_index(drop=True)

        df_rolling = rolling_mean.merge(rolling_stdev, on="date", how="outer")
        df_rolling = df_rolling.fillna(value=0)
        return df_rolling
