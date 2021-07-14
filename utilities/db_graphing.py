import os

import pandas as pd


def add_files(DIR, filepaths):
    files = os.listdir(DIR)
    for file in files:
        if ".csv" in file or 'all_gpu' in file and "all" not in file:
            filepaths.append(DIR + file)
    return filepaths


def find_all_filepaths():
    all_filepaths = []
    for DIR in DIRS:
        add_files(DIR, all_filepaths)
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
    frame = frame.dropna(axis='columns')

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
    card_dict = [card for card in card_dicts if card['index'] == index][0]
    return card_dict


def clean_dataframe(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.drop_duplicates()
    try:
        df = df.drop(['s-item__trending-price'], axis=1)
    except BaseException:
        pass
    try:
        df = df.drop(['s-item__deliveryOptions'], axis=1)
    except BaseException:
        pass
    return df
