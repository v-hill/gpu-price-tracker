import datetime
import json
import os

import matplotlib.colors as mplc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import ceil
from sqlalchemy import create_engine

from configuration import DATABASE_NAME, PATHS

# Load plotting spec file
spec_filepath = "src/analysis/gpu_plots.json"
with open(spec_filepath) as input_file:
    plots_dict = json.load(input_file)

# Load in database


# SQLAlchemy connectable
cnx = create_engine(f"sqlite:///{DATABASE_NAME}").connect()

df_log = pd.read_sql_table("log", cnx)  # Log table
df_gpu = pd.read_sql_table("gpu", cnx)  # GPU table
df_sale = pd.read_sql_table("sale", cnx)  # Sale table

df = df_sale.merge(df_gpu, on=["gpu_id"], how="left")


# remove duplicate entries
print(df.shape)
df = df.drop_duplicates(
    subset=["bids", "price", "postage", "title", "date", "name"]
)
print(df.shape)


def remove_outliers(df, col):
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)

    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    out_df = df.loc[(df[col] > lower_bound) & (df[col] < upper_bound)]
    return out_df


def apply_dict_filters(df, card_dict, filter_title=True, clean_outliers=True):
    df = df[
        df["name"].str.contains(card_dict["search_term"].replace("_", " "))
    ]

    if filter_title:
        df = df[
            df["title"].str.contains(
                card_dict["search_term"].replace("_", " ")
            )
        ]

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
        df = remove_outliers(df, "total_price")

    if len(df) == 0:
        raise Exception("No data left after filters")
    return df


for index, filters in enumerate(plots_dict):
    # index = 27
    # filters = plots_dict[index]

    df_subset = apply_dict_filters(
        df, filters, filter_title=True, clean_outliers=True
    )

    # average across a number of days
    average_period = 14  # set the number of days to average by
    df_subset["day_count"] = (
        (df_subset["date"] - pd.to_datetime(datetime.date(2020, 1, 1)))
        .astype("timedelta64[D]")
        .astype(int)
    )

    df_subset["day_group"] = ceil(
        (df_subset["day_count"].values / average_period)
    )

    df_subset["num_sold"] = 1

    df_subset["date_int"] = pd.to_datetime(df_subset["date"]).view(np.int64)

    agg_dict = {
        "bids": "mean",
        "price": "mean",
        "postage": "mean",
        "total_price": "mean",
        "date_int": "max",
        "num_sold": "sum",
        "day_group": "mean",
    }

    df_average = (
        df_subset.groupby(["day_group"]).agg(agg_dict).reset_index(drop=True)
    )

    df_average.rename(columns={"date_int": "date"}, inplace=True)
    df_average["date"] = pd.to_datetime(df_average["date"])

    cmap = mplc.LinearSegmentedColormap.from_list(
        "", [[0.25, 1, 0.25], [1, 0.25, 0.25]]
    )

    fig = plt.figure(figsize=(10, 6), dpi=200)
    ax = fig.add_subplot(111)

    ax.grid(color="gray", linestyle="dashed", which="both", alpha=0.5)

    x_axis = "date"
    y_axis = "total_price"
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
