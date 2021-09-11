"""
Module for miscellaneous utilities.
"""

# Python library imports
from datetime import datetime


def too_old(conf: dict, data_items: list):
    """
    Given the date_limit in the configuration.toml file, test whether the
    items in the data_items list are older than this limit.

    Parameters
    ----------
    conf : dict
        configuration.toml
    data_items : list
        List of EbayItem objects.

    Returns
    -------
    bool
        True if there are items in data_items which are older than the date
        limit from the .toml config.
    """
    date_limit_str = conf["date_limit"]["oldest"]
    date_limit = datetime.strptime(date_limit_str, "%Y-%m-%d")
    oldest_sale = datetime.now()
    for item in data_items:
        if item.item_attributes["date"] < oldest_sale:
            oldest_sale = item.item_attributes["date"]
    if oldest_sale < date_limit:
        # print(f'    oldest: {oldest_sale}, limit: {date_limit}') # For debug
        return True
    return False


def check_always_accepted(name: str, conf: dict):
    """
    Check if the GPU name contains one the always_accept filters set in the
    configuration.toml file.

    Parameters
    ----------
    name : str
        GPU name
    conf : dict
        configuration.toml

    Returns
    -------
    bool
        True if GPU contains an always accepted string, else False.
    """
    filters = [f.lower() for f in conf["filters"]["always_accept"]]
    if any(x in name.lower() for x in filters):
        return True
    return False


def remove_unicode(input_string: str):
    """
    Function that takes in a string and removes any unicode characters.

    Parameters
    ----------
    input_string : str
        The string to remove unicode from.

    Returns
    -------
    str
        String with unicode removed.
    """
    strencode = input_string.encode("ascii", "ignore")
    strdecode = strencode.decode()
    return strdecode
