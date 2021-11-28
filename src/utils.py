"""
Module for miscellaneous utilities.
"""

import logging
from datetime import datetime


def too_old(date_limit: dict, data_items: list):
    """
    Given the date_limit in the configuration.toml file, test whether the
    items in the data_items list are older than this limit.

    Parameters
    ----------
    date_limit : dict
        The dictionary of limits for how old an item can be and still be added
        to the database.
    data_items : list
        List of EbayItem objects.

    Returns
    -------
    bool
        True if there are items in data_items which are older than the date
        limit from the .toml config.
    """
    date_limit_str = date_limit["oldest"]
    date_limit = datetime.strptime(date_limit_str, "%Y-%m-%d")
    oldest_sale = datetime.now()
    for item in data_items:
        if item.item_attributes["date"] < oldest_sale:
            oldest_sale = item.item_attributes["date"]
    if oldest_sale < date_limit:
        logging.debug(
            f"    oldest: {oldest_sale}, limit: {date_limit}"
        )  # For debug
        return True
    return False


def check_always_accepted(name: str, filters: dict):
    """
    Check if the GPU name contains one the always_accept filters set in the
    configuration.

    Parameters
    ----------
    name : str
        GPU name
    filters : dict
        Dict containing accepted_substrings strings and always_accept strings

    Returns
    -------
    bool
        True if GPU contains an always accepted string, else False.
    """
    filters = [f.lower() for f in filters["always_accept"]]
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
