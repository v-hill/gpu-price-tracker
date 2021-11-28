import datetime
import json
import os

import numpy as np
import pandas as pd
from numpy import ceil

from src.configuration import PATHS

# Load plotting spec file
spec_filepath = "analysis/gpu_plots.json"
with open(spec_filepath) as input_file:
    plots_dict = json.load(input_file)

# Load in database
database_filename = "combined_gpu_db.json"
files = os.listdir(PATHS["filepath"])
if database_filename not in files:
    raise Exception(f"{database_filename} is not in the data folder")
database_filepath = os.path.join(PATHS["filepath"], database_filename)
with open(database_filepath) as input_file:
    data = json.load(input_file)

df = pd.json_normalize(
    data=data["collected"],
    record_path="data",
    meta=[
        "name",
        "collection_time",
        "num_sold",
    ],
)

# clean price, postage and total price
cols_float = ["price", "postage"]
df[cols_float] = df[cols_float].astype(str)
df_cols = df[cols_float].copy()
df[df_cols.columns] = df_cols.apply(
    lambda x: x.str.encode("ascii", "ignore").str.decode("ascii")
)
df[cols_float] = df[cols_float].apply(pd.to_numeric, errors="coerce")
df[cols_float] = df[cols_float].fillna(0)
df["total price"] = df["price"] + df["postage"]

# clean title
cols_str = ["title"]
df[cols_str] = df[cols_str].astype(str)
df_cols = df[cols_str].copy()
df[df_cols.columns] = df_cols.apply(
    lambda x: x.str.encode("ascii", "ignore").str.decode("ascii")
)

# clean dates
df["date"] = pd.to_datetime(df["date"])
df["collection_time"] = pd.to_datetime(df["collection_time"])

# clean num_sold
df["num_sold"] = df["num_sold"].astype(int)

# remove duplicate entries
df = df.drop_duplicates(subset=["bids", "price", "postage", "title", "date", "name"])


def remove_outliers(df, col):
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)

    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    out_df = df.loc[(df[col] > lower_bound) & (df[col] < upper_bound)]
    return out_df


def apply_dict_filters(df, card_dict, filter_title=True, clean_outliers=True):
    df = df[df["name"].str.contains(card_dict["search_term"].replace("_", " "))]

    if filter_title:
        df = df[df["title"].str.contains(card_dict["search_term"].replace("_", " "))]

    if card_dict["gb_required"] is not False:
        df = df[df["title"].str.contains(card_dict["gb_required"])]
    if card_dict["gb_exclude"] is not False:
        df = df[~df["title"].str.contains(card_dict["gb_exclude"])]

    if card_dict["new"]:
        df = df[df["title"].str.contains("New|new")]
    else:
        df = df[~df["title"].str.contains("New|new")]

    if card_dict["super"]:
        df = df[df["title"].str.contains("SUPER|uper|0 s|0 S")]
    else:
        df = df[~df["title"].str.contains("SUPER|uper|0 s|0 S")]

    if card_dict["ti"]:
        df = df[df["title"].str.contains(" TI| Ti| ti|0T|0t|-T|-t")]
    else:
        df = df[~df["title"].str.contains(" TI| Ti| ti|0T|0t|-T|-t")]

    if card_dict["mini"]:
        df = df[df["title"].str.contains("Mini|mini")]
    else:
        df = df[~df["title"].str.contains("Mini|mini")]

    if card_dict["founders"]:
        df = df[df["title"].str.contains("Founders|founders")]
    else:
        df = df[~df["title"].str.contains("Founders|founders")]

    if clean_outliers:
        df = remove_outliers(df, "total price")

    if len(df) == 0:
        raise Exception("No data left after filters")
    return df


list_of_dataframes = []

for index, filters in enumerate(plots_dict):
    df_subset = apply_dict_filters(df, filters, filter_title=True, clean_outliers=True)

    # average across a number of days
    average_period = 30.41666  # set the number of days to average by
    df_subset["month_count"] = (
        (df_subset["date"] - pd.to_datetime(datetime.date(2020, 1, 1)))
        .astype("timedelta64[D]")
        .astype(int)
    )

    df_subset["month_group"] = ceil((df_subset["month_count"].values / average_period))

    df_subset["num_sold"] = 1

    df_subset["date_int"] = pd.to_datetime(df_subset["date"]).astype(np.int64)

    agg_dict = {
        "bids": "mean",
        "price": "mean",
        "postage": "mean",
        "total price": "mean",
        "date_int": "max",
        "num_sold": "sum",
        "month_group": "mean",
    }

    df_average = df_subset.groupby(["month_group"]).agg(agg_dict).reset_index(drop=True)

    df_average.rename(columns={"date_int": "date"}, inplace=True)
    df_average["date"] = pd.to_datetime(df_average["date"])
    df_average["title"] = filters["title"]
    list_of_dataframes.append(df_average)

df_final = pd.concat(list_of_dataframes)
print(df_final.shape)
