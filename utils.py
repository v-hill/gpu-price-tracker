"""
Module for miscellaneous utilities.
"""

# Python library imports
from datetime import datetime


def too_old(conf, data_items):
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
    date_limit_str = conf['date_limit']['oldest']
    date_limit = datetime.strptime(date_limit_str, '%Y-%m-%d')
    oldest_sale = datetime.now()
    for item in data_items:
        if item.item_attributes['date'] < oldest_sale:
            oldest_sale = item.item_attributes['date']
    if oldest_sale < date_limit:
        # print(f'    oldest: {oldest_sale}, limit: {date_limit}') # For debug
        return True
    return False
