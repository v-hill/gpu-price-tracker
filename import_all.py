"""
Main script importing historic data.
"""
import datetime
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

os.chdir(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

import django

django.setup()

import pandas as pd
from django.utils.timezone import make_aware

from scraper.models import EbayGraphicsCard, Log, Sale
from scraper.src.scraper import (
    calculate_sales_added_per_log,
    calculate_total_collected_per_gpu,
)

df_log = pd.read_csv("log.csv")
df_gpu = pd.read_csv("gpu.csv")
df_sale = pd.read_csv("sale.csv")


print(df_sale.shape)

df_sale = df_sale.drop_duplicates(
    subset=[
        # "sale_id",
        # "log_id",
        "gpu_id",
        "title",
        "bids",
        "date",
        "postage",
        "price",
        "total_price",
    ],
    keep="last",
)

print(df_sale.shape)


# for id in range(1, 40):
#     count = df_sale[df_sale["log_id"]==id].shape[0]
#     print(id, count)


Log.objects.all().delete()
for index, row in df_log.iterrows():
    try:
        sales_scraped = int(row["sales_scraped"])
    except:
        sales_scraped = 0

    new_record = Log(
        id=row["log_id"],
        start_time=make_aware(
            datetime.datetime.strptime(
                row["start_time"].split(".")[0], "%Y-%m-%d %H:%M:%S"
            )
        ),
        end_time=make_aware(
            datetime.datetime.strptime(
                row["end_time"].split(".")[0], "%Y-%m-%d %H:%M:%S"
            )
        ),
        sales_scraped=sales_scraped,
        sales_added=int(df_sale[df_sale["log_id"] == row["log_id"]].shape[0]),
    )
    new_record.save()
    print(row["log_id"])

EbayGraphicsCard.objects.all().delete()
for index, row in df_gpu.iterrows():
    new_record = EbayGraphicsCard(
        id=row["gpu_id"],
        log=Log.objects.filter(pk=row["log_id"]).first(),
        name=row["name"],
        data_collected=bool(row["data_collected"]),
        last_collection=make_aware(
            datetime.datetime.strptime(
                row["last_collection"].split(".")[0], "%Y-%m-%d %H:%M:%S"
            )
        ),
    )
    new_record.save()
    print(row["name"])


Sale.objects.all().delete()
new_records = []
for index, row in df_sale.iterrows():
    new_record = Sale(
        id=int(row["sale_id"]),
        log=Log.objects.filter(pk=row["log_id"]).first(),
        gpu=EbayGraphicsCard.objects.filter(pk=row["gpu_id"]).first(),
        title=row["title"],
        bids=int(row["bids"]),
        date=make_aware(
            datetime.datetime.strptime(
                row["date"].split(".")[0], "%Y-%m-%d %H:%M:%S"
            )
        ),
        postage=round(float(row["postage"]), 2),
        price=round(float(row["price"]), 2),
        total_price=round(float(row["total_price"]), 2),
    )
    new_records.append(new_record)

    if index % 5000 == 0:
        Sale.objects.bulk_create(new_records)
        new_records = []
        print(f"{index:>5} / {len(df_sale)}")

Sale.objects.bulk_create(new_records)
new_records = []
print(f"{index:>5} / {len(df_sale)}")

calculate_total_collected_per_gpu()
print("-" * 79)
calculate_sales_added_per_log()
