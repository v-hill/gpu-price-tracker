"""
Module for miscellaneous utilities.
"""
import re


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


def check_num_results_bounds(num_results: int, num_results_limits: dict):
    if num_results <= num_results_limits["min"]:
        return False
    if num_results >= num_results_limits["max"]:
        raise Exception(
            "Too many results found, navigation to GPU page unsuccessful"
        )
    return True


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


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return days, hours, minutes, seconds


def generate_time_since_str(days, hours, minutes, seconds):
    time_since_str = "    "
    if days > 1:
        time_since_str += f"{days} days "
    elif days == 1:
        time_since_str += f"{days} day "
    if hours > 1 or hours == 0:
        time_since_str += f"{hours} hours "
    elif hours == 1:
        time_since_str += f"{hours} hour "
    if minutes > 1 or minutes == 0:
        time_since_str += f"{minutes} minutes "
    elif minutes == 1:
        time_since_str += f"{minutes} minute "
    if days == 0 and hours == 0 and minutes <= 30:
        if seconds > 1 or seconds == 0:
            time_since_str += f"{seconds} seconds "
        elif seconds == 1:
            time_since_str += f"{seconds} second "
    time_since_str += "since last run"
    return time_since_str


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, True
    else:
        instance = model(**kwargs)
        return instance, False


def sort_price_str(price):
    try:
        price_num = float(price)
        return price
    except:
        test_val = str(price).replace(",", "")
        if any(map(test_val.lower().__contains__, ["free", "collect"])):
            price_num = float(0)
        else:
            test_val = remove_unicode(test_val)
            price_list = re.findall(r"\d*\.?\d+", test_val)
            if len(price_list) != 1:
                raise Exception("price list contains more than one element")
            price_num = float(price_list[0])
        return price_num
