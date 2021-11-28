import datetime
import json
import os

import matplotlib.colors as mplc
import matplotlib.pyplot as plt
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


for index, filters in enumerate(plots_dict):
    # index = 27
    # filters = plots_dict[index]

    df_subset = apply_dict_filters(df, filters, filter_title=True, clean_outliers=True)

    # average across a number of days
    average_period = 14  # set the number of days to average by
    df_subset["day_count"] = (
        (df_subset["date"] - pd.to_datetime(datetime.date(2020, 1, 1)))
        .astype("timedelta64[D]")
        .astype(int)
    )

    df_subset["day_group"] = ceil((df_subset["day_count"].values / average_period))

    df_subset["num_sold"] = 1

    df_subset["date_int"] = pd.to_datetime(df_subset["date"]).view(np.int64)

    agg_dict = {
        "bids": "mean",
        "price": "mean",
        "postage": "mean",
        "total price": "mean",
        "date_int": "max",
        "num_sold": "sum",
        "day_group": "mean",
    }

    df_average = df_subset.groupby(["day_group"]).agg(agg_dict).reset_index(drop=True)

    df_average.rename(columns={"date_int": "date"}, inplace=True)
    df_average["date"] = pd.to_datetime(df_average["date"])

    cmap = mplc.LinearSegmentedColormap.from_list(
        "", [[0.25, 1, 0.25], [1, 0.25, 0.25]]
    )

    fig = plt.figure(figsize=(10, 6), dpi=200)
    ax = fig.add_subplot(111)

    ax.grid(color="gray", linestyle="dashed", which="both", alpha=0.5)

    x_axis = "date"
    y_axis = "total price"
    plt.xlabel(x_axis.title())
    plt.ylabel(y_axis.title())
    plt.title(f'{filters["title"]}', fontsize=14)

    plt.text(
        0.025,
        0.9,
        f"Latest {y_axis} average: £{df_average[y_axis].values[-1]:0.2f}",
        fontsize=12,
        transform=ax.transAxes,
    )

    plt.scatter(
        df_average[x_axis],
        df_average[y_axis],
        c=df_average[y_axis],
        cmap=cmap,
        alpha=0.7,
        s=10,
    )

    x2, y2 = 0, -10
    for i, txt in enumerate(df_average["num_sold"]):
        # if i%2==0:
        #     continue

        ax.annotate(
            f"{txt:0.0f}",
            (df_average[x_axis].values[i], df_average[y_axis].values[i]),
            xycoords="data",
            xytext=(x2, y2),
            textcoords="offset points",
            fontsize=8,
            alpha=0.5,
        )

    plt.plot(df_average[x_axis], df_average[y_axis], "--", c=[0.25, 0.25, 1])
    plt.savefig(f"{PATHS['filepath']}/{filters['title'].replace(' ','_')}.png")
    print(index, filters["title"], df_average["num_sold"].sum())
    print(" ")
