import os

import pandas as pd


def add_files(DIR, filepaths):
    files = os.listdir(DIR)
    for file in files:
        if ".csv" in file or "all_gpu" in file and "all" not in file:
            filepaths.append(DIR + file)
    return filepaths


def find_all_filepaths(dirs):
    all_filepaths = []
    for dir in dirs:
        add_files(dir, all_filepaths)
    return all_filepaths


def get_card_names(all_filepaths):
    cards = []
    for name in all_filepaths:
        card = name.split("\\")[-1]
        card = card.split("GPU_Model_")[-1]

        if card not in cards:
            cards.append(card)
    return cards


def get_card(sub_string, paths):
    filepaths = []
    for file in paths:
        if sub_string in file:
            filepaths.append(file)
    return filepaths


def make_df(filepaths):
    li = []

    for filename in filepaths:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)

    frame = pd.concat(li, axis=0, ignore_index=True)
    frame = frame.drop_duplicates()
    frame = frame.dropna(axis="columns")

    return frame.reset_index(drop=True)


def remove_outlier(df, col):
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)

    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (2.5 * iqr)

    out_df = df.loc[(df[col] > lower_bound) & (df[col] < upper_bound)]
    return out_df


def select_from_card_dict(index, card_dicts):
    card_dict = [card for card in card_dicts if card["index"] == index][0]
    return card_dict


def clean_dataframe(df):
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.drop_duplicates()
    try:
        df = df.drop(["s-item__trending-price"], axis=1)
    except BaseException:
        pass
    try:
        df = df.drop(["s-item__deliveryOptions"], axis=1)
    except BaseException:
        pass
    return df


def apply_dict_filters(df, card_dict, filter_title=True):
    if filter_title:
        df = df[
            df["Product title"].str.contains(
                card_dict["search_term"].replace("_", "")
            )
        ]

    if card_dict["gb_required"] is not False:
        df = df[df["Product title"].str.contains(card_dict["gb_required"])]
    if card_dict["gb_exclude"] is not False:
        df = df[~df["Product title"].str.contains(card_dict["gb_exclude"])]

    if card_dict["new"]:
        df = df[df["Product title"].str.contains("New|new")]
    else:
        df = df[~df["Product title"].str.contains("New|new")]

    if card_dict["super"]:
        df = df[df["Product title"].str.contains("SUPER|uper|0 s|0 S")]
    else:
        df = df[~df["Product title"].str.contains("SUPER|uper|0 s|0 S")]

    if card_dict["ti"]:
        df = df[df["Product title"].str.contains(" TI| Ti| ti|0T|0t|-T|-t")]
    else:
        df = df[~df["Product title"].str.contains(" TI| Ti| ti|0T|0t|-T|-t")]

    if card_dict["mini"]:
        df = df[df["Product title"].str.contains("Mini|mini")]
    else:
        df = df[~df["Product title"].str.contains("Mini|mini")]

    if card_dict["founders"]:
        df = df[df["Product title"].str.contains("Founders|founders")]
    else:
        df = df[~df["Product title"].str.contains("Founders|founders")]

    if card_dict["remove_outliers"]:
        df = remove_outlier(df, "Total price")

    df = df.rename(
        columns={
            "s-item__bidCount": "Bid count",
            "s-item__logisticsCost": "Postage price",
            "s-item__price": "Item price",
        }
    )

    df = df.drop(["POSITIVE"], axis=1)
    df = df.drop_duplicates()

    if len(df) == 0:
        raise Exception("No data left after filters")
    return df


def make_weeks(start, end):
    weeks = []
    for week in pd.date_range(start, end, freq="W"):
        weeks.append(week)
    return weeks


def calc_weekly_prices(weeks, data1):
    prices = []
    dates = []
    for i in range(len(weeks) - 1):
        start = weeks[i]
        end = weeks[i + 1]
        df_temp = data1[(data1["Date"] < end) & (data1["Date"] > start)]
        if len(df_temp) > 3:
            mean1 = float(f"{df_temp['Total price'].mean():0.2f}")
            # stdev1 = float(f"{df_temp['Total price'].std():0.1f}")
            print(
                f"{start:%Y %b %d}    {len(df_temp):5} sold    "
                "£{mean1:6} \u00B1 {stdev1}"
            )
            prices.append(mean1)
            dates.append(start + (end - start) / 2)
    return dates, prices
